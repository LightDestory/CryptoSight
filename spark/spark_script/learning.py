from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
from pyspark import SparkContext
from pyspark.sql.functions import from_json, col, to_timestamp, unix_timestamp, window
from pyspark.sql.types import StructType, TimestampType, DoubleType
from sklearn.linear_model import LinearRegression
from elasticsearch import Elasticsearch
import pandas as pd


coins = ['bitcoin', 'binancecoin', 'dogecoin', 'ripple', 'ethereum', 'tether', "cardano"]
model_dictionary = {}

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
        .add('bitcoin_circulating_supply', DoubleType(), True) \
        .add('bitcoin_current_price_usd', DoubleType(), True) \
        .add('tether_circulating_supply', DoubleType(), True) \
        .add('bitcoin_current_price_eur', DoubleType(), True) \
        .add('binancecoin_circulating_supply', DoubleType(), True) \
        .add('ethereum_market_cap', DoubleType(), True) \
        .add('tether_market_cap', DoubleType(), True) \
        .add('binancecoin_current_price_usd', DoubleType(), True) \
        .add('ripple_current_price_eur', DoubleType(), True) \
        .add('ethereum_current_price_eur', DoubleType(), True) \
        .add('binancecoin_current_price_eur', DoubleType(), True) \
        .add('cardano_market_cap', DoubleType(), True) \
        .add('ethereum_circulating_supply', DoubleType(), True) \
        .add('dogecoin_current_price_eur', DoubleType(), True) \
        .add('dogecoin_current_price_usd', DoubleType(), True) \
        .add('ripple_current_price_usd', DoubleType(), True) \
        .add('ripple_circulating_supply', DoubleType(), True) \
        .add('binancecoin_market_cap', DoubleType(), True) \
        .add('ripple_market_cap', DoubleType(), True) \
        .add('ethereum_current_price_usd', DoubleType(), True) \
        .add('tether_current_price_usd', DoubleType(), True) \
        .add('cardano_current_price_eur', DoubleType(), True) \
        .add('dogecoin_market_cap', DoubleType(), True) \
        .add('@timestamp', TimestampType(), True) \
        .add('tether_current_price_eur', DoubleType(), True) \
        .add('cardano_current_price_usd', DoubleType(), True) \
        .add('cardano_circulating_supply', DoubleType(), True) \
        .add('dogecoin_circulating_supply', DoubleType(), True) \
        .add('bitcoin_market_cap', DoubleType(), True)


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
            col('bitcoin_current_price_usd'),
            col('binancecoin_current_price_usd'),
            col('dogecoin_current_price_usd'),
            col('ripple_current_price_usd'),
            col('ethereum_current_price_usd'),
            col('tether_current_price_usd'),
            col('cardano_current_price_usd')
        )


def get_resulting_df_schema():
    return StructType() \
        .add("@timestamp", TimestampType()) \
        .add('bitcoin_estimated_price_usd', DoubleType()) \
        .add('binancecoin_estimated_price_usd', DoubleType()) \
        .add('dogecoin_estimated_price_usd', DoubleType()) \
        .add('ripple_estimated_price_usd', DoubleType()) \
        .add('ethereum_estimated_price_usd', DoubleType()) \
        .add('tether_estimated_price_usd', DoubleType()) \
        .add('cardano_estimated_price_usd', DoubleType())


def get_output_df():
    return pd.DataFrame(columns=[
        '@timestamp',
        'bitcoin_estimated_price_usd',
        'binancecoin_estimated_price_usd',
        'dogecoin_estimated_price_usd',
        'ripple_estimated_price_usd',
        'ethereum_estimated_price_usd',
        'tether_estimated_price_usd',
        'cardano_estimated_price_usd'
    ])


def generate_linear_regression_models(df: pd.DataFrame):
    x = df['milliseconds'].to_numpy().reshape(-1, 1)
    for coin in coins:
        y = df[f"{coin}_current_price_usd"].to_numpy()
        lr = LinearRegression()
        lr.fit(x, y)
        model_dictionary[coin] = lr


def make_series(timestamp, price_dictionary) -> pd.Series:
    return pd.Series([
        str(timestamp),
        float(price_dictionary[coins[0]]),
        float(price_dictionary[coins[1]]),
        float(price_dictionary[coins[2]]),
        float(price_dictionary[coins[3]]),
        float(price_dictionary[coins[4]]),
        float(price_dictionary[coins[5]]),
        float(price_dictionary[coins[6]])
    ], index=[
        '@timestamp',
        'bitcoin_estimated_price_usd',
        'binancecoin_estimated_price_usd',
        'dogecoin_estimated_price_usd',
        'ripple_estimated_price_usd',
        'ethereum_estimated_price_usd',
        'tether_estimated_price_usd',
        'cardano_estimated_price_usd'
    ])


def predict_value(milliseconds):
    """rssi_range = lambda s: max(min(0, s), -120)
    s = model.predict([[milliseconds]])[0]
    return rssi_range(s)
    """
    estimation = {}
    for coin in coins:
        estimation[coin] = 999999
    return estimation


def predict(df: pd.DataFrame) -> pd.DataFrame:
    nrows = lambda df: df.shape[0]
    newdf = get_output_df()
    if (nrows(df) < 1):
        return newdf
    generate_linear_regression_models(df)
    lastCryptoSnapshot = df['milliseconds'].values.max()
    next_minutes = [(lastCryptoSnapshot + (60000 * i)) for i in range(5)]
    next_prices = [predict_value(m) for m in next_minutes]
    for millis, price_dictionary in zip(next_minutes, next_prices):
        newdf = newdf.append(make_series(millis, price_dictionary), ignore_index=True)
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
                "bitcoin_estimated_price_usd": {"type": "double"},
                "binancecoin_estimated_price_usd": {"type": "double"},
                "dogecoin_estimated_price_usd": {"type": "double"},
                "ripple_estimated_price_usd": {"type": "double"},
                "ethereum_estimated_price_usd": {"type": "double"},
                "tether_estimated_price_usd": {"type": "double"},
                "cardano_estimated_price_usd": {"type": "double"}
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
        .groupBy(win) \
        .applyInPandas(predict, get_resulting_df_schema()) \
        .writeStream \
        .option('checkpointLocation', '/tmp/checkpoint') \
        .format('es') \
        .start('crypto-prediction-spark') \
        .awaitTermination()
