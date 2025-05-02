# from datetime import datetime
# from airflow.models import DAG
# from airflow.operators.bash import BashOperator
# from S3_minio.sensor.s3connectionsensor import S3ConnectionSensor
# from S3_minio.operator.paginatedhttptos3operator import PaginatedHttpToS3Operator

# def decide_branch(**kwargs):
#     # Логика ветвления на основе контекста выполнения
#     if kwargs['execution_date'].weekday() in [5, 6]:  # выходные
#         return 'weekend_task'
#     else:
#         return 'weekday_task'

# default_args = {
#     "owner": "market",
#     "depends_on_past": False,
#     "start_date": datetime(2025, 3, 21),
#     #"retry_delay": timedelta(minutes=0.1)
# }

# with dag = DAG('dag_test_sensor', 
#         default_args=default_args, 
#         schedule_interval='0 1 * * *', 
#         catchup=True,
#         max_active_tasks=2, 
#         max_active_runs=1, 
#         tags=["Test", "My first sensor"]
#     )

#     test_sensor = S3ConnectionSensor(
#         task_id="check_s3_connection",
#         aws_conn_id="minio_conn",
#         bucket_name="data.lake",
#         poke_interval=30,  # Проверка каждые 30 секунд
#         timeout=300, 
#         dag=dag
#     )
#     get_data_from_api = PaginatedHttpToS3Operator(
#         task_id="get_data_from_api",
#         http_conn_id='API_OZON_transaction_list',
#         endpoint='/v3/finance/transaction/list',
#         method='POST',
#         data=json.dumps({
#             'filter': 'active',
#             'sort': 'date'
#         }),
#         headers={'Content-Type': 'application/json'},
#         s3_conn_id='s3_conn',
#         s3_bucket='my-data-bucket',
#         s3_key='raw_data/{ds}/page_{page}.json',
#         pagination_param='page_num',
#         page_size=500,
#         max_pages=50,
#         delay_between_pages=0.5,
#         pagination_callback=custom_pagination_callback,
#         replace=False
#         dag=dag
#     )
    
#     test_sensor