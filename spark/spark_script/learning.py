from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
from pyspark import SparkContext
from pyspark.sql.functions import from_json, col, to_timestamp, unix_timestamp, window
from pyspark.sql.types import StructType, TimestampType, DoubleType
from sklearn.linear_model import LinearRegression
from elasticsearch import Elasticsearch
import pandas as pd


def get_spark_session():
    spark_conf = SparkConf() \
        .set('es.nodes', 'opensearch') \
        .set('es.port', '9200')
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
        .load()