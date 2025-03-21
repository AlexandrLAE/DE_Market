from datetime import datetime
from airflow.models import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "market",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 21),
    #"retry_delay": timedelta(minutes=0.1)
}

dag = DAG('dag_test_1', default_args=default_args, schedule_interval='0 1 * * *', catchup=True,
          max_active_tasks=2, max_active_runs=1, tags=["Test", "My first dag"])

task1 = BashOperator(
    task_id='task1',
    bash_command='python3 /opt/airflow/scripts/task1.py',
    dag=dag)

task2 = BashOperator(
    task_id='task2',
    bash_command='python3 /opt/airflow/scripts/task2.py',
    dag=dag)

task1 >> task2