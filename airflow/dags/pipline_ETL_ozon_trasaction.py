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

@dag(start_date=datetime(2023, 1, 1), schedule_interval=None, default_args=default_args)

def pipline_ETL_ozon_trazaction_list():

    
        
   