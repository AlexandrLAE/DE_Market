# from airflow.decorators import dag, task
# from datetime import datetime, timedelta
# from airflow.providers.amazon.aws.hooks.s3 import S3Hook
# from airflow.hooks.base import BaseHook
# from airflow.exceptions import AirflowException
# import requests
# import json
# import uuid
# import time
# import tempfile
# import os
# from typing import Dict, Any, Optional, Tuple
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# from dataclasses import dataclass
# import structlog
# from collections import defaultdict

# # Настройка structlog
# structlog.configure(
#     processors=[
#         structlog.stdlib.filter_by_level,
#         structlog.stdlib.add_logger_name,
#         structlog.stdlib.add_log_level,
#         structlog.stdlib.PositionalArgumentsFormatter(),
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.StackInfoRenderer(),
#         structlog.processors.format_exc_info,
#         structlog.processors.UnicodeDecoder(),
#         structlog.processors.JSONRenderer()
#     ],
#     context_class=dict,
#     logger_factory=structlog.stdlib.LoggerFactory(),
#     wrapper_class=structlog.stdlib.BoundLogger,
#     cache_logger_on_first_use=True,
# )

# # Получение логгера
# logger = structlog.get_logger(__name__)

# # Конфигурация
# DEFAULT_PAGE_SIZE = 1000
# MAX_PAGES = 1000
# BASE_DELAY = 0.5
# MAX_RETRY_ATTEMPTS = 3
# RETRY_DELAY = timedelta(minutes=5)
# API_TIMEOUT = (20, 30)  # connect timeout, read timeout

# default_args = {
#     "owner": "market",
#     "depends_on_past": False,
#     "start_date": datetime(2025, 3, 21),
#     "retries": MAX_RETRY_ATTEMPTS,
#     "retry_delay": RETRY_DELAY,
#     "max_active_tis_per_dag": 1,
#     "catchup": False
# }


# class APIConnectionError(Exception):
#     """Кастомное исключение для ошибок подключения к API"""
#     pass

# class DataValidationError(Exception):
#     """Ошибка валидации данных"""
#     pass

# @dag(
#     schedule_interval="@daily",
#     default_args=default_args,
#     catchup=False,
#     max_active_runs=1,
#     tags=["ozon", "etl"],
#     doc_md="""### DAG для загрузки транзакций из Ozon в MinIO
#     Ежедневно загружает данные транзакций за предыдущий день"""
# )
# def pipeline_ETL_ozon_transaction_list():

#     @retry(
#         stop=stop_after_attempt(3),
#         wait=wait_exponential(multiplier=1, min=4, max=10),
#         retry=retry_if_exception_type((requests.RequestException, APIConnectionError)),
#         before_sleep=lambda retry_state: logger.warning(
#             "retrying_request",
#             exception=str(retry_state.outcome.exception()),
#             attempt=retry_state.attempt_number)
#     )
#     def make_api_request(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
#         """Выполнение запроса к API с повторными попытками"""
#         try:
#             logger.info("making_api_request", url=url, payload=str(json.dumps(payload)[:200])
#             response = requests.post(
#                 url,
#                 json=payload,
#                 headers=headers,
#                 timeout=API_TIMEOUT
#             )
            
#             if response.status_code == 429:
#                 retry_after = int(response.headers.get("Retry-After", 10))
#                 logger.warning("rate_limit_exceeded", wait_seconds=retry_after)
#                 time.sleep(retry_after)
#                 raise APIConnectionError("Rate limit - retrying")
                
#             response.raise_for_status()
#             return response
            
#         except requests.RequestException as e:
#             logger.error("request_failed", error=str(e))
#             raise

#     @task(retries=2, retry_delay=timedelta(minutes=1))
#     def verify_minio_connection() -> bool:
#         """Проверка подключения и доступности MinIO"""
#         try:
#             s3_hook = S3Hook(aws_conn_id='minio_conn')
#             bucket_name = 'data.lake'
            
#             if not s3_hook.check_for_bucket(bucket_name):
#                 raise AirflowException(f"Target bucket '{bucket_name}' not found")
                
#             # Проверка прав на запись
#             test_key = f"test_connection_{uuid.uuid4().hex[:8]}.txt"
#             test_content = "connection_test"
            
#             try:
#                 s3_hook.load_string(
#                     string_data=test_content,
#                     bucket_name=bucket_name,
#                     key=test_key,
#                     replace=True
#                 )
                
#                 # Проверка чтения
#                 downloaded = s3_hook.read_key(
#                     key=test_key,
#                     bucket_name=bucket_name
#                 )
                
#                 if downloaded != test_content:
#                     raise AirflowException("Data integrity check failed")
                
#                 # Удаление тестового файла
#                 s3_hook.delete_objects(bucket_name=bucket_name, keys=[test_key])
                
#                 logger.info("minio_connection_verified")
#                 return True
                
#             except Exception as e:
#                 raise AirflowException(f"MinIO read/write verification failed: {str(e)}")
                
#         except Exception as e:
#             logger.error("minio_verification_failed", error=str(e))
#             raise

#     def validate_api_response(data: Dict[str, Any]) -> bool:
#         """Валидация структуры ответа API"""
#         if not isinstance(data, dict):
#             raise DataValidationError("API response is not a dictionary")
            
#         if "result" not in data:
#             raise DataValidationError("Missing 'result' key in API response")
            
#         result = data["result"]
#         if "operations" not in result:
#             raise DataValidationError("Missing 'operations' key in API result")
            
#         if not isinstance(result["operations"], list):
#             raise DataValidationError("Operations should be a list")
            
#         return True

#     def generate_s3_paths(execution_date: datetime) -> Tuple[str, str]:
#         """Генерация путей для сохранения в S3"""
#         date_prefix = execution_date.strftime("%Y/%m/%d")
#         file_id = f"{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
#         data_key = f"ozon/transactions/{date_prefix}/data_{file_id}.json"
#         meta_key = f"ozon/transactions/{date_prefix}/meta_{file_id}.json"
        
#         return data_key, meta_key

#     def cleanup_temp_files(*files):
#         """Удаление временных файлов"""
#         for file in files:
#             if file and os.path.exists(file):
#                 try:
#                     os.unlink(file)
#                     logger.debug("deleted_temp_file", file_path=file)
#                 except Exception as e:
#                     logger.warning("error_deleting_temp_file", file_path=file, error=str(e))

#     @task(retries=MAX_RETRY_ATTEMPTS, retry_delay=RETRY_DELAY)
#     def extract_and_load_transactions(**context) -> Dict[str, Any]:
#         """Основная ETL задача: извлечение и загрузка данных"""
#         execution_date = context["execution_date"]
#         start_date = execution_date.strftime('%Y-%m-%dT00:00:00Z')
#         end_date = (execution_date + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z')
        
#         # Получение параметров подключения
#         conn = BaseHook.get_connection("API_OZON_warehouse_list")
#         extra_data = conn.extra_dejson 
#         client_id = extra_data.get("Client-Id")
#         api_key = extra_data.get("api_key")
#         url = conn.host
        
#         if not all([client_id, api_key, url]):
#             raise AirflowException("Missing required API connection parameters")

#         headers = {
#             "Client-Id": client_id, 
#             "Api-Key": api_key,
#             "Content-Type": "application/json"
#         }
        
#         payload_template = {
#             "filter": {
#                 "date": {"from": start_date, "to": end_date},
#                 "transaction_type": "all"
#             },
#             "page_size": DEFAULT_PAGE_SIZE
#         }

#         # Создание временных файлов
#         data_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False)
#         meta_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.meta', delete=False)
        
#         data_path = data_file.name
#         meta_path = meta_file.name
        
#         try:
#             current_page = 1
#             max_pages = None
#             stats = defaultdict(int)

#             while current_page <= MAX_PAGES:
#                 try:
#                     payload = {**payload_template, "page": current_page}
#                     response = make_api_request(url, headers, payload)
#                     data = response.json()
                    
#                     # Валидация ответа
#                     validate_api_response(data)
                    
#                     operations = data["result"]["operations"]
#                     if not operations:
#                         logger.info("empty_page_detected")
#                         break
                    
#                     # Запись данных
#                     for op in operations:
#                         try:
#                             json_line = json.dumps(op, ensure_ascii=False)
#                             data_file.write(json_line + '\n')
#                             stats["total_records"] += 1
#                         except (TypeError, ValueError) as e:
#                             logger.warning("serialization_failed", error=str(e))
#                             stats["failed_records"] += 1
#                             continue

#                     # Проверка пагинации
#                     if max_pages is None and "page_count" in data.get("result", {}):
#                         max_pages = min(data["result"]["page_count"], MAX_PAGES)
#                         logger.info("total_pages_detected", pages=max_pages)
                    
#                     if max_pages and current_page >= max_pages:
#                         logger.info("reached_last_page")
#                         break
                        
#                     current_page += 1
#                     time.sleep(BASE_DELAY)
                    
#                 except DataValidationError as e:
#                     logger.error("data_validation_error", error=str(e))
#                     raise
#                 except Exception as e:
#                     logger.error("unexpected_error", error=str(e))
#                     raise

#             # Сохранение метаданных
#             json.dump(dict(stats), meta_file, indent=2)
#             data_file.close()
#             meta_file.close()

#             # Генерация путей и загрузка в MinIO
#             data_key, meta_key = generate_s3_paths(execution_date)
#             s3_hook = S3Hook(aws_conn_id='minio_conn')
            
#             try:
#                 s3_hook.load_file(
#                     filename=data_path,
#                     bucket_name='data.lake',
#                     key=data_key,
#                     replace=True,
#                     encrypt=False
#                 )
#                 s3_hook.load_file(
#                     filename=meta_path,
#                     bucket_name='data.lake',
#                     key=meta_key,
#                     replace=True,
#                     encrypt=False
#                 )
                
#                 logger.info(
#                     "data_loaded_successfully",
#                     records=stats["total_records"],
#                     s3_path=data_key
#                 )
                
#                 return {
#                     "data_path": data_key,
#                     "meta_path": meta_key,
#                     "stats": dict(stats)
#                 }
                
#             except Exception as e:
#                 logger.error("minio_upload_failed", error=str(e))
#                 raise AirflowException(f"MinIO upload failed: {e}")
                
#         finally:
#             # Гарантированное закрытие файлов
#             for f in [data_file, meta_file]:
#                 try:
#                     if not f.closed:
#                         f.close()
#                 except Exception as e:
#                     logger.warning("error_closing_file", error=str(e))
            
#             # Удаление временных файлов
#             cleanup_temp_files(data_path, meta_path)

#     # Оркестрация задач
#     minio_check = verify_minio_connection()
#     etl_process = extract_and_load_transactions()
    
#     minio_check >> etl_process

# # Инициализация DAG
# ozon_transactions_etl = pipeline_ETL_ozon_transaction_list()