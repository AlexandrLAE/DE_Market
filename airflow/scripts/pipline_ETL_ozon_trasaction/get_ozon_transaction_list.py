from airflow.decorators import task
from datetime import datetime
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base_hook import BaseHook
import requests
import json


@task
def get_ozon_tranzaction_list():
        conn = BaseHook.get_connection("API_OZON_transaction_list")
        extra_data = conn.extra_dejson 
        client_id = extra_data.get("Client-Id")
        api_key = extra_data.get("api_key")
        content_type = extra_data.get("Content-Type")
        url = {conn.host}
        
        headers = {
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": content_type
        }

        start_date = datetime.datetime(2023, 10, 1)
        end_date = datetime.datetime(2023, 10, 31)
        current_page = 1
        all_operations = []
        
        while True:
            payload = {
                "filter": {
                    "date": {
                        "from": start_date.strftime("%Y-%m-%dT00:00:00.000Z"),
                        "to": end_date.strftime("%Y-%m-%dT23:59:59.999Z")
                    }
                },
                "page": current_page,
                "page_size": 1000  # Максимальное количество элементов на странице
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            all_operations.extend(data["result"]["operations"])
            
            if current_page >= data["result"]["page_count"]:
                break
            current_page += 1
        
        
        if response.status_code == 200:
            # Сохраняем JSON в файл
            with open("/home/jovyan/data_lake/warehouse_list_.json", "w") as file: #уточнить место хранения при использовании airflow
                json.dump(all_operations.json(), file)
        else:
            print(f"Ошибка: {response.status_code}")

        def get_accruals(start_date, end_date, client_id, api_key):
        
        
        

    
    

    transactions = get_accruals(start_date, end_date, client_id, api_key)
    print(f"Всего транзакций: {len(transactions)}")