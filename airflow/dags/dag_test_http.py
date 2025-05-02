from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.models import Variable
import json
from datetime import datetime


default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 5, 2),
    
}

dag = DAG('test_http', default_args=default_args, schedule_interval='0 1 * * *', catchup=True,
          max_active_tasks=1, max_active_runs=1, tags=["test_connection"])

v_client_id = Variable.get("client_id_ozon_password")
v_api = Variable.get("api_ozon_password")

task_post = SimpleHttpOperator(
    task_id="post_data",
    method="POST",
    endpoint="",
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
            "page": 1,
            "page_size": 10
            }),
    headers={
            "Client-Id": v_client_id,
            "Api-Key": v_api,
            "Content-Type": "application/json"
            },
    http_conn_id="API_OZON_transaction_list",
    response_check=lambda response: (
    response.status_code in [200, 201] and 
    response.json().get('status') == 'OK'
),
    dag=dag
)

task_post 