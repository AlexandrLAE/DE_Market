from airflow import DAG
from airflow.models import Variable
import json
from datetime import datetime
from S3_minio.operator.paginatedhttptos3operator import PaginatedHttpToS3Operator
from S3_minio.sensor.s3connectionsensor import S3ConnectionSensor

def get_api_dates(**context):
    logical_date = context["data_interval_start"]  
    
    # Расчёт дат
    start_date = logical_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = logical_date.replace(hour=23, minute=59, second=59, microsecond=999)
    
    # Форматирование в ISO 8601 с UTC (Z)
    return {
        "start_date": start_date.isoformat(timespec="milliseconds") + "Z",
        "end_date": end_date.isoformat(timespec="milliseconds") + "Z",
    }

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 5, 1),
    "retries": 1,
}

with  DAG('dag_ETL_ozon', 
        #owner="market",
        #start_date=datetime(2025, 5, 1),
        schedule_interval='0 0 * * *', 
        #catchup=True,
        max_active_tasks=2, 
        max_active_runs=1, 
         default_args=default_args,
        tags=["market", "dowload"]
    ) as dag:
 
    v_client_id = Variable.get("client_id_ozon_password")
    v_api = Variable.get("api_ozon_password")

    check_s3 = S3ConnectionSensor(
            task_id='check_s3_data',
            aws_conn_id='minio_conn',
            bucket_name='data.lake',
            dag=dag)

    pload_data = PaginatedHttpToS3Operator(
            task_id='upload_paginated_data',
            http_conn_id='API_OZON_transaction_list',
            endpoint='/v3/finance/transaction/list',
            method='POST',
            data=json.dumps({
                "filter": {
                "date": {
                "from": "{{ data_interval_start.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S.000Z') }}",
                "to": "{{ data_interval_start.replace(hour=23, minute=59, second=59, microsecond=999).strftime('%Y-%m-%dT%H:%M:%S.999Z') }}"
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
            replace=True,
            dag=dag)

check_s3 >> pload_data