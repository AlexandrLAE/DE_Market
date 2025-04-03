from airflow.decorators import dag, task
from datetime import datetime
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base_hook import BaseHook
import requests
import json

default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 21),
    #"retry_delay": timedelta(minutes=0.1)
}

@dag(schedule_interval=@daily, default_args=default_args)

def pipline_ETL_ozon_trazaction_list():
    

    @task
    def test_minio_connection():
        hook = S3Hook(aws_conn_id='minio_conn')
        s3 = hook.get_conn()
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            print(f"Bucket: {bucket['Name']}")
    
    
    def get_data_from_api(start_date, end_date):  # API_OZON_warehouse_list
        conn = BaseHook.get_connection("API_OZON_warehouse_list")
        extra_data = conn.extra_dejson 
        client_id = extra_data.get("Client-Id")
        api_key = extra_data.get("api_key")
        content_type = extra_data.get("Content-Type")
        url = {conn.host}
        date_from = start_date
        date_to = end_date
        payload = {
                "filter": {
                "date": {
                "from": "2025-03-27T00:00:00.000Z",
                "to": "2025-03-28T00:00:00.000Z"
                },
                "operation_type": [ ],
                "posting_number": "",
                "transaction_type": "all"
                },
                "page": 1,
                "page_size": 1000
                }
        headers = {
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": content_type
        }
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            # Сохраняем JSON в файл
            with open("/home/jovyan/data_lake/warehouse_list_.json", "w") as file: #уточнить место хранения при использовании airflow
                json.dump(response.json(), file)
        else:
            print(f"Ошибка: {response.status_code}")
