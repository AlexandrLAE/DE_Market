from datetime import datetime
from airflow.models import DAG
from airflow.operators.bash import BashOperator
from S3_minio.sensor.s3connectionsensor import S3ConnectionSensor


default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 21),
    #"retry_delay": timedelta(minutes=0.1)
}

dag = DAG('dag_test_sensor', 
    default_args=default_args, 
    schedule_interval='0 1 * * *', 
    catchup=True,
    max_active_tasks=2, 
    max_active_runs=1, 
    tags=["Test", "My first sensor"]
    )

test_sensor = S3ConnectionSensor(
    task_id="check_s3_connection",
    aws_conn_id="my_aws_conn",
    poke_interval=30,  # Проверка каждые 30 секунд
    timeout=300, 
    )
  
test_sensor