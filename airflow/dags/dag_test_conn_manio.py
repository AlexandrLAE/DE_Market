from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_minio_connection():
    hook = S3Hook(aws_conn_id='minio_conn')
    buckets = hook.list_buckets()  # Получаем список бакетов
    print(f"Доступные бакеты в MinIO: {buckets}")

default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 28),
    #"retry_delay": timedelta(minutes=0.1)
}

dag = DAG('test_minio', default_args=default_args, schedule_interval='0 1 * * *', catchup=True,
          max_active_tasks=2, max_active_runs=1, tags=["test_minio_connection"])

task1 = PythonOperator (
    task_id='test_minio',
        python_callable=test_minio_connection,
        dag=dag)

task1 

