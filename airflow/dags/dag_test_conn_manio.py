from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from datetime import datetime

import boto3
from airflow.hooks.base import BaseHook

def test_minio_connection():
    conn = BaseHook.get_connection('Minio')

    s3 = boto3.resource('s3',
                        endpoint_url=conn.host,
                        aws_access_key_id=conn.login,
                        aws_secret_access_key=conn.password
    )
    s3client = s3.meta.client 
    hook = s3.get_conn()

    #and then you can use boto3 methods for manipulating buckets and files
    #for example:

    bucket = s3.Bucket('ozon')
    # Iterates through all the objects, doing the pagination for you. Each obj
    # is an ObjectSummary, so it doesn't contain the body. You'll need to call
    # get to get the whole body.
    for obj in bucket.objects.all():
        key = obj.key
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

