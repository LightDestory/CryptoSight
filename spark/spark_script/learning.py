from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
from pyspark import SparkContext
from pyspark.sql.functions import from_json, col, to_timestamp, unix_timestamp, window
from pyspark.sql.types import StructType, StringType, DoubleType
from sklearn.linear_model import LinearRegression
from elasticsearch import Elasticsearch
import pandas as pd


def get_spark_session():
    spark_conf = SparkConf() \
        .set('es.nodes', 'https://opensearch') \
        .set('es.port', '9200') \
        .set("es.net.http.auth.user","admin") \
        .set("es.net.http.auth.pass", "admin") \
        .set('es.net.ssl', 'true') \
        .set('es.nodes.wan.only', 'true') \
        .set('es.nodes.resolve.hostname', "false") \
        .set("es.net.ssl.cert.allow.self.signed", "true") \
        .set("es.nodes.discovery", "false") \
        .set("es.spark.sql.streaming.sink.log.enabled", "false")
    sc = SparkContext(appName='crypto_prediction', conf=spark_conf)
    return SparkSession(sc)


def get_cryptocurrency_data_schema():
    return StructType() \
        .add('@timestamp', StringType(), True) \
        .add('coin', StringType(), True) \
        .add('circulating_supply', DoubleType(), True) \
        .add('total_volume', DoubleType(), True) \
        .add('market_cap', DoubleType(), True) \
        .add('current_price', DoubleType(), True)


def get_cryptocurrency_kafka_data_stream(schema: StructType):
    return spark.readStream \
        .format('kafka') \
        .option('kafka.bootstrap.servers', 'kafkaserver:9092') \
        .option('subscribe', 'cryptocurrencies') \
        .option("kafka.group.id", "spark-consumer") \
        .load() \
        .select('timestamp', 'value') \
        .withColumn('time', to_timestamp('timestamp', 'YYYY/MM/DD hh:mm:ss')) \
        .withColumn('json_content', col('value').cast('string')) \
        .withColumn('content', from_json(col('json_content'), schema)) \
        .select(col('time'), col('content.*')) \
        .withColumn('milliseconds', unix_timestamp('@timestamp', format="yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")) \
        .select(
            col('time'),
            col('@timestamp'),
            col('milliseconds'),
            col('coin'),
            col('current_price')
        )


def get_resulting_df_schema():
    return StructType() \
        .add("@timestamp", StringType()) \
        .add("coin", StringType()) \
        .add('estimated_price', DoubleType())


def get_output_df():
    return pd.DataFrame(columns=[
        '@timestamp',
        'coin',
        'estimated_price'
    ])


def generate_linear_regression_model(df: pd.DataFrame):
    x = df['milliseconds'].to_numpy().reshape(-1, 1)
    y = df["current_price"].to_numpy()
    lr = LinearRegression()
    lr.fit(x, y)
    return lr


def make_series(df, timestamp, estimated_price) -> pd.Series:
    return pd.Series([
        str(timestamp),
        df.iloc[0]['coin'],
        float(estimated_price)
    ], index=[
        '@timestamp',
        'coin',
        'estimated_price'
    ])


def predict_value(model, milliseconds):
    return model.predict([[milliseconds]])[0]


def predict(df: pd.DataFrame) -> pd.DataFrame:
    nrows = lambda df: df.shape[0]
    newdf = get_output_df()
    if (nrows(df) < 1):
        return newdf
    model = generate_linear_regression_model(df)
    lastCryptoSnapshot = df['milliseconds'].values.max()
    next_minutes = [(lastCryptoSnapshot + (60000 * i)) for i in range(5)]
    next_prices = [predict_value(model, m) for m in next_minutes]
    for millis, price in zip(next_minutes, next_prices):
        newdf = newdf.append(make_series(df, millis, price), ignore_index=True)
    return newdf


if __name__ == "__main__":
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("ERROR")
    dataSchema = get_cryptocurrency_data_schema()
    dataStream = get_cryptocurrency_kafka_data_stream(dataSchema)

    es_mapping = {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date", "format": "epoch_second"},
                "coin": {
                    "type": "text", 
                    "fields": {
                        "keyword": { 
                            "type": "keyword"
                        }
                    }
                },
                "estimated_price": {"type": "double"}
            }
        }
    }

    es = Elasticsearch(['https://admin:admin@opensearch:9200'], verify_certs=False)
    response = es.indices.create(
        index='crypto-prediction-spark',
        body=es_mapping,
        ignore=400
    )

    # Check Index Creation
    if 'acknowledged' in response:
        if response['acknowledged']:
            print("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])
    # catch API error response
    elif 'error' in response:
        print("ERROR:", response['error']['root_cause'])
        print("TYPE:", response['error']['type'])

    win = window(dataStream.time, "1 minutes")
    dataStream \
        .groupBy('coin', win) \
        .applyInPandas(predict, get_resulting_df_schema()) \
        .writeStream \
        .option('checkpointLocation', '/tmp/checkpoint') \
        .format('es') \
        .start('crypto-prediction-spark') \
        .awaitTermination()
