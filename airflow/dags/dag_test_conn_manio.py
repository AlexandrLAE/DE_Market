from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_minio_connection():
    hook = S3Hook(aws_conn_id='minio_conn')
    buckets = hook.list_buckets()  # Получаем список бакетов
    print(f"Доступные бакеты в MinIO: {buckets}")

with DAG('test_minio_connection', start_date=datetime(2025, 3, 28)) as dag:
    test_task = PythonOperator(
        task_id='test_minio',
        python_callable=test_minio_connection
    )