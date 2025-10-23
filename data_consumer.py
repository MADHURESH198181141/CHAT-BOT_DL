import json
from kafka import KafkaConsumer
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
import happybase
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# If config not loaded (e.g., when run from outside directory), try absolute path
if not config.sections():
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)

# Kafka configuration
bootstrap_servers = config['kafka']['bootstrap_servers']
topic = config['kafka']['topic']

# HBase configuration
hbase_host = config['hbase']['host']
hbase_port = int(config['hbase']['port'])
table_name = config['hbase']['table']

# Initialize Spark session
spark = SparkSession.builder \
    .appName("PatientDataConsumer") \
    .getOrCreate()

# Define schema for patient data
schema = StructType([
    StructField("patient_id", StringType()),
    StructField("heart_rate", IntegerType()),
    StructField("temperature", FloatType()),
    StructField("blood_pressure", StringType()),
    StructField("oxygen_saturation", IntegerType()),
    StructField("timestamp", StringType())
])

def process_batch(df, epoch_id):
    """Process each batch of data from Kafka."""
    # Convert JSON strings to structured data
    parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    # Store all patient data in HBase
    parsed_df.foreachPartition(store_in_hbase)

    print(f"Processed batch {epoch_id}: {parsed_df.count()} records")

def store_in_hbase(partition):
    """Store data in HBase."""
    connection = happybase.Connection(hbase_host, hbase_port)
    table = connection.table(table_name)

    for row in partition:
        row_key = f"{row.patient_id}_{row.timestamp}"
        data = {
            'vitals:heart_rate': str(row.heart_rate),
            'vitals:temperature': str(row.temperature),
            'vitals:blood_pressure': row.blood_pressure,
            'vitals:oxygen_saturation': str(row.oxygen_saturation),
            'vitals:timestamp': row.timestamp
        }
        table.put(row_key, data)

    connection.close()

def main():
    # Initialize Kafka consumer
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[bootstrap_servers],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='patient_monitor_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    # Create HBase table if it doesn't exist
    connection = happybase.Connection(hbase_host, hbase_port)
    if table_name.encode() not in connection.tables():
        connection.create_table(table_name, {'vitals': dict()})
    connection.close()

    print("Starting patient data consumer...")

    # Read from Kafka using Spark Structured Streaming
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", topic) \
        .load()

    # Process the stream
    query = df.writeStream \
        .foreachBatch(process_batch) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
