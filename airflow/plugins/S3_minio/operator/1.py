from airflow.providers.http.operators.http import HttpOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.models import Variable
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta


class MyPaginatedHttpToS3Operator(HttpOperator):
    """
    Кастомный оператор для загрузки данных через POST с пагинацией и сохранения в S3
    
    :param endpoint: API endpoint URL
    :param headers: HTTP headers including Client-Id and Api-Key
    :param request_params: Parameters for the POST request body
    :param s3_bucket: Target S3 bucket name
    :param s3_key: Target S3 key (path) template (can include {date}, {page}, etc.)
    :param pagination_page_size: Number of items per page (default: 100)
    :param date_range_days: Number of days to fetch data for (default: 30)
    :param start_date: Optional start date (default: execution_date - date_range_days)
    :param end_date: Optional end date (default: execution_date)
    """
    
    template_fields = ('s3_key', 'start_date', 'end_date')
    
    def __init__(
        self,
        endpoint: str,
        headers: Dict[str, str],
        request_params: Dict,
        s3_bucket: str,
        s3_key: str,
        pagination_page_size: int = 100,
        date_range_days: int = 30,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            endpoint=endpoint,
            method='POST',
            headers=headers,
            **kwargs
        )
        
        self.request_params = request_params
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.pagination_page_size = pagination_page_size
        self.date_range_days = date_range_days
        self.start_date = start_date
        self.end_date = end_date
        
    def execute(self, context):
        execution_date = context['execution_date']
        
        # Calculate date range
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d') if self.end_date else execution_date
        start_date = (
            datetime.strptime(self.start_date, '%Y-%m-%d') 
            if self.start_date 
            else end_date - timedelta(days=self.date_range_days)
        )
        
        # Ensure we don't exceed 1 month limit
        if (end_date - start_date).days > 30:
            raise ValueError("Maximum period for one request is 1 month (30 days)")
        
        # Format dates for API
        date_filter = {
            "date": {
                "from": start_date.strftime('%Y-%m-%d'),
                "to": end_date.strftime('%Y-%m-%d')
            }
        }
        
        s3_hook = S3Hook()
        page = 1
        total_rows = 0
        
        while True:
            # Prepare request body with pagination
            request_body = {
                "filter": date_filter,
                "page": page,
                "page_size": self.pagination_page_size,
                **self.request_params
            }
            
            self.log.info(f"Fetching page {page} for period {start_date} to {end_date}")
            
            # Make POST request
            response = self.run(
                data=json.dumps(request_body),
                headers=self.headers
            )
            
            response_data = json.loads(response.text)
            
            # Check if we got data
            if not response_data.get('result', {}).get('operations'):
                self.log.info("No more data found")
                break
                
            # Save to S3
            s3_key = self.s3_key.format(
                date=execution_date.strftime('%Y-%m-%d'),
                page=page,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            s3_hook.load_string(
                string_data=json.dumps(response_data),
                key=s3_key,
                bucket_name=self.s3_bucket,
                replace=True
            )
            
            self.log.info(f"Saved page {page} to s3://{self.s3_bucket}/{s3_key}")
            
            # Update counters
            total_rows += len(response_data['result']['operations'])
            page_count = response_data.get('result', {}).get('page_count', 0)
            row_count = response_data.get('result', {}).get('row_count', 0)
            
            # Check if we've processed all pages
            if page >= page_count or total_rows >= row_count:
                break
                
            page += 1
            
        self.log.info(f"Finished processing. Total rows processed: {total_rows}")