from airflow.decorators import dag, task
from datetime import datetime, timedelta
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base import BaseHook
import requests
import json
import uuid
import time
import tempfile
import os

default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 21),
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

@dag(
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=["ozon", "etl"]
)
def pipline_ETL_ozon_transaction_list():

    @task
    def test_minio_connection():
        """Проверка подключения к MinIO"""
        try:
            s3_hook = S3Hook(aws_conn_id='minio_conn')
            buckets = s3_hook.list_buckets()
            print(f"Успешное подключение. Доступные бакеты: {buckets}")
            return True
        except Exception as e:
            print(f"Ошибка подключения к MinIO: {e}")
            raise

    @task
    def extract_and_load_ozon_transactions(**context):
        """Извлечение данных транзакций из Ozon API и загрузка в MinIO"""
        execution_date = context["execution_date"]
        start_date = execution_date.strftime('%Y-%m-%dT00:00:00Z')
        end_date = (execution_date + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z')
        
        try:
            # Инициализация подключения к API
            conn = BaseHook.get_connection("API_OZON_warehouse_list")
            extra_data = conn.extra_dejson 
            client_id = extra_data.get("Client-Id")
            api_key = extra_data.get("api_key")
            url = conn.host
            
            if not all([client_id, api_key, url]):
                raise ValueError("Отсутствуют необходимые параметры подключения")

            headers = {
                "Client-Id": client_id,
                "Api-Key": api_key,
            }

            payload_template = {
                "filter": {
                    "date": {"from": start_date, "to": end_date},
                    "operation_type": [],
                    "posting_number": "",
                    "transaction_type": "all"
                },
                "page_size": 1000
            }

            # Создаем временный файл для хранения данных
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
                temp_file_path = tmp_file.name
                
                current_page = 1
                max_pages = None
                total_records = 0
                metadata = {
                    "date_range": f"{start_date} - {end_date}",
                    "pages_processed": 0,
                    "total_records": 0
                }

                while current_page <= 1000:  # Максимальное количество страниц
                    print(f"Обрабатывается страница {current_page}...")
                    payload = {**payload_template, "page": current_page}
                    
                    try:
                        response = requests.post(
                            url, 
                            json=payload, 
                            headers=headers, 
                            timeout=20
                        )
                        
                        # Обработка ограничения скорости
                        if response.status_code == 429:
                            retry_after = int(response.headers.get("Retry-After", 10))
                            print(f"Превышен лимит запросов. Ожидание {retry_after} сек...")
                            time.sleep(retry_after)
                            continue
                            
                        response.raise_for_status()
                        data = response.json()
                        
                        # Валидация структуры ответа
                        if not isinstance(data.get("result", {}).get("operations", []), list):
                            raise ValueError("Некорректный формат данных операций")
                        
                        operations = data["result"]["operations"]
                        if not operations:
                            print("Пустая страница - завершение")
                            break
                        
                        # Записываем данные во временный файл
                        for operation in operations:
                            tmp_file.write(json.dumps(operation) + '\n')
                            total_records += 1
                        
                        # Обновление информации о страницах
                        if max_pages is None and "page_count" in data["result"]:
                            max_pages = data["result"]["page_count"]
                            print(f"Всего страниц: {max_pages}")
                        
                        if max_pages and current_page >= max_pages:
                            print("Достигнута последняя страница")
                            break
                            
                        current_page += 1
                        time.sleep(1)  # Базовая задержка между запросами
                        
                    except requests.HTTPError as e:
                        if e.response.status_code >= 500:
                            print(f"Ошибка сервера, повтор через 10 сек...")
                            time.sleep(10)
                            continue
                        raise
                    except requests.RequestException as e:
                        print(f"Ошибка сети: {e}. Повтор через 5 сек...")
                        time.sleep(5)
                        continue

                metadata.update({
                    "pages_processed": current_page,
                    "total_records": total_records
                })

                # Сохраняем метаданные в отдельный файл
                metadata_file_path = temp_file_path + '.meta'
                with open(metadata_file_path, 'w') as meta_file:
                    json.dump(metadata, meta_file)

            # Загрузка данных в MinIO
            s3_hook = S3Hook(aws_conn_id='minio_conn')
            date_str = execution_date.strftime("%Y-%m-%d")
            
            # Загружаем основные данные
            data_key = (
                f"ozon/transactions/"
                f"{date_str}/"
                f"transactions_{execution_date.timestamp()}_{uuid.uuid4().hex[:6]}.json"
            )
            s3_hook.load_file(
                filename=temp_file_path,
                bucket_name='data.lake',
                key=data_key,
                replace=True
            )
            
            # Загружаем метаданные
            meta_key = data_key + '.meta'
            s3_hook.load_file(
                filename=metadata_file_path,
                bucket_name='data.lake',
                key=meta_key,
                replace=True
            )
            
            print(f"Данные успешно загружены в {data_key}")
            print(f"Метаданные загружены в {meta_key}")
            
            # Удаляем временные файлы
            os.unlink(temp_file_path)
            os.unlink(metadata_file_path)
            
            return {
                "data_key": data_key,
                "meta_key": meta_key,
                "record_count": total_records
            }
            
        except Exception as e:
            print(f"Ошибка в процессе извлечения и загрузки: {e}")
            # Удаляем временные файлы в случае ошибки
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if 'metadata_file_path' in locals() and os.path.exists(metadata_file_path):
                os.unlink(metadata_file_path)
            raise

    # Оркестрация задач
    connection_test = test_minio_connection()
    extract_load_task = extract_and_load_ozon_transactions()
    
    connection_test >> extract_load_task

# Создаем DAG
ozon_transactions_dag = pipline_ETL_ozon_transaction_list()