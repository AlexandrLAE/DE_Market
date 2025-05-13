from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'daily_etl_pipeline',
    default_args=default_args,
    description='Daily ETL pipeline with Spark',
    schedule_interval=None,
    catchup=False
)

spark_task = SparkSubmitOperator(
    task_id="spark_job",
    application="/path/to/your/spark/app.py",  # путь к приложению
    name="spark_job_name",  # имя приложения
    conn_id="spark_default",  # соединение с Spark
    verbose=False,  # подробный вывод
    conf={
        'spark.executor.memory': '4G',
        'spark.executor.cores': '1',
        'spark.executor.instances': '1'
    },  # конфигурация Spark
    application_args=["arg1", "arg2"],  # аргументы приложения
    jars="/path/to/jar1.jar,/path/to/jar2.jar",  # дополнительные JAR-файлы
    py_files="/path/to/dependency.py,/path/to/another.py",  # Python-зависимости
    files="/path/to/file1,/path/to/file2",  # дополнительные файлы
    driver_memory="1G",  # память драйвера
    executor_memory="1G",  # память исполнителя
    executor_cores=1,  # ядра на исполнителя
    num_executors=2,  # количество исполнителей
    total_executor_cores=2,  # общее количество ядер
    queue="default",  # очередь ресурсов
    deploy_mode="client",  # режим деплоя (client/cluster)
    keytab="/path/to/keytab",  # путь к keytab-файлу
    principal="user@DOMAIN",  # principal для Kerberos
    proxy_user="user",  # пользователь для impersonation
    java_class="com.example.MainClass",  # основной класс Java
    packages="com.example:package:1.0.0",  # Maven-пакеты
    exclude_packages="org.exclude:package",  # исключаемые пакеты
    repositories="http://repo.example.com",  # репозитории
    archives="/path/to/archive.zip",  # архивы
    env_vars={"ENV_VAR": "value"},  # переменные окружения
    driver_classpath="/path/to/driver/classpath",  # classpath драйвера
    properties_file="/path/to/spark/properties.conf"  # файл свойств
)