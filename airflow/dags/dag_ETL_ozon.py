from airflow import DAG
from airflow.models import Variable
import json
from datetime import datetime
from S3_minio.operator.paginatedhttptos3operator import PaginatedHttpToS3Operator
from S3_minio.sensor.s3connectionsensor import S3ConnectionSensor

def decide_branch(**kwargs):
    # Логика ветвления на основе контекста выполнения
    if kwargs['execution_date'].weekday() in [5, 6]:  # выходные
        return 'weekend_task'
    else:
        return 'weekday_task'

default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 5, 1),

}

dag = DAG('dag_test_sensor', 
        default_args=default_args, 
        schedule_interval='0 0 * * *', 
        #catchup=True,
        max_active_tasks=2, 
        max_active_runs=1, 
        tags=["market", "dowload"]
    )
 
v_client_id = Variable.get("client_id_ozon_password")
v_api = Variable.get("api_ozon_password")

check_s3 = S3ConnectionSensor(
    task_id='check_s3_data',
    http_conn_id='minio_conn',
    bucket_name='data.lake',
    dag=dag,
)



pload_data = PaginatedHttpToS3Operator(
        task_id='upload_paginated_data',
        http_conn_id='API_OZON_transaction_list',
        endpoint='/v3/finance/transaction/list',
        method='POST',
        data=json.dumps({
            "filter": {
            "date": {
            "from": "2025-03-27T00:00:00.000Z",
            "to": "2025-03-28T00:00:00.000Z"
            },
            "operation_type": [ ],
            "posting_number": "",
            "transaction_type": "all"
            },
         
            }),
        headers={
            "Client-Id": v_client_id,
            "Api-Key": v_api,
            "Content-Type": "application/json"
            },
        s3_conn_id='minio_conn',
        s3_bucket='data.lake',
        s3_key='ozon/finance/transaction/list/{ds}/page_{page}.json',
        page_size=10,
        end_pages=500,
        delay_between_pages=5,
        replace=False,
        dag=dag,
)

check_s3 >> pload_data