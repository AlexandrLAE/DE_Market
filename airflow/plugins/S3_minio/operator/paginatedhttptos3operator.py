from typing import Optional, Dict, Any
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.http.hooks.http import HttpHook
from airflow.models import BaseOperator
import json
import time

class PaginatedHttpToS3Operator(SimpleHttpOperator):
    """
    Кастомный оператор для загрузки данных через POST с пагинацией и сохранения в S3    
    :param s3_conn_id: S3 connection ID
    :param s3_bucket: S3 bucket name
    :param s3_key: S3 key template (содержит {page} для номера страницы)
    :param page_size: количество элементов на странице (default: 1000)
    :param end_pages: последняя и/или максимальное количество страниц (default: 1000 - защита от бесконечного цикла)
    :param start_page: начальная страница (default: 30)

    :param delay_between_pages: задержка между запросами (в секундах)
    :param pagination_callback: функция для определения наличия следующей страницы
    :param request_params: Parameters for the POST request body
    """
    
    template_fields = SimpleHttpOperator.template_fields + ('s3_bucket', 's3_key', 'start_page', 'page_size', 'end_pages')
    
    def __init__(
        self,
        s3_conn_id: str,
        s3_bucket: str,
        s3_key: str,
        name_page_size: str='page_size',
        page_size: int = 1000,
        end_pages: int = 1000,
        name_start_page: str='page',
        start_page: int = 1,
        replace: bool = True,
        delay_between_pages: float = 5.0,
        pagination_callback: Optional[callable] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.s3_conn_id = s3_conn_id
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.name_page_size = name_page_size
        self.page_size = page_size
        self.end_pages = end_pages
        self.name_start_page = name_start_page
        self.start_page = start_page
        self.replace = replace
        self.delay_between_pages = delay_between_pages
        self.pagination_callback = pagination_callback or self.default_pagination_callback
        self.http_hook = None
        
    def default_pagination_callback(self, response: Any) -> bool:
        """Определяет по умолчанию есть ли следующая страница"""
        if response.status_code != 200:
            return False
        if not response.text.strip():
            return False
        try:
            data = response.json()
            if isinstance(data, list):
                return bool(data)  # Непустой ли список
            if isinstance(data, dict):
                return bool(data)  # Непустой ли словарь
            return False
        except (json.JSONDecodeError, AttributeError):
            return False
    
    def get_http_hook(self):
        """Инициализирует и возвращает HTTP hook"""
        if self.http_hook is None:
            self.http_hook = HttpHook(
                method=self.method,
                http_conn_id=self.http_conn_id
            )
        return self.http_hook

    def execute(self, context: Dict):
        http_hook = self.get_http_hook()
        s3_hook = S3Hook(aws_conn_id=self.s3_conn_id)
        has_more = True
        page = self.start_page

        original_data = json.loads(self.data) if isinstance(self.data, str) else (self.data or {})
        
        while has_more and page <= self.end_pages:
            try:
                # Формируем payload с текущей страницей
                payload = {
                    **original_data,
                    self.name_start_page:  page,
                    self.name_page_size: self.page_size                    
                }
                
                # Выполняем запрос
                self.log.info(f"Fetching page {page}")
                response = http_hook.run(
                    endpoint=self.endpoint,
                    data=json.dumps(payload),
                    headers=self.headers
                )
                
                response.raise_for_status()
                
                # Проверяем есть ли еще данные
                has_more = self.pagination_callback(response)
                
                
                # Пауза между запросами
                if has_more and self.delay_between_pages > 0:
                    # Формируем S3 ключ
                    s3_key = self.s3_key.format(
                        page=page,
                        **context
                    )
                    
                    # Загружаем в S3
                    s3_hook.load_string(
                        string_data=response.text,
                        key=s3_key,
                        bucket_name=self.s3_bucket,
                        replace=self.replace
                    )
                    
                    self.log.info(f"Successfully uploaded page {page} to s3://{self.s3_bucket}/{s3_key}")

                    page += 1

                    time.sleep(self.delay_between_pages)
                    
            except Exception as e:
                self.log.error(f"Error processing page {page}: {str(e)}")
                raise

#Example 
#  upload_data = PaginatedHttpToS3Operator(
#         task_id='upload_paginated_data',
#         http_conn_id='API_OZON_transaction_list',
#         endpoint='/v3/finance/transaction/list',
#         method='POST',
#         data=json.dumps({
            # "filter": {
            # "date": {
            # "from": "2025-03-27T00:00:00.000Z",
            # "to": "2025-03-28T00:00:00.000Z"
            # },
            # "operation_type": [ ],
            # "posting_number": "",
            # "transaction_type": "all"
            # },
         
            # }),
#         headers={
            # "Client-Id": v_client_id,
            # "Api-Key": v_api,
            # "Content-Type": "application/json"
            # },
#         s3_conn_id='minio_conn',
#         s3_bucket='data.lake',
#         s3_key='ozon/finance/transaction/list/{ds}/page_{page}.json',
#         page_size=10,
#         end_pages=500,
#         delay_between_pages=5,
#         replace=False,
#         dag=dag
#     )