FROM jupyter/pyspark-notebook:spark-3.1.1

RUN pip3 install pyspark kafka-utils numpy "elasticsearch==7.13.4" pandas scikit-learn

WORKDIR /app

RUN mkdir -p "/tmp/checkpoint"

COPY ./spark_script/learning.py .

# Run commands
ENTRYPOINT ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1,org.elasticsearch:elasticsearch-spark-30_2.12:7.12.1", "/app/learning.py"]