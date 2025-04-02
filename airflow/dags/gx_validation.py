from datetime import datetime
from airflow.decorators import dag, task
from great_expectations.data_context import FileDataContext

@dag(
    schedule="@daily",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    default_args={
        "retries": 2,
        "on_failure_callback": lambda ctx: send_alert(ctx)
    }
)
def s3_data_quality_dag():

    @task
    def validate_s3_data():
        context = FileDataContext("/opt/airflow/gx")
        result = context.run_checkpoint(
            checkpoint_name="daily_validation",
            batch_request={
                "datasource_name": "s3_datasource",
                "data_asset_name": "{{ var.value.S3_DATA_PATH }}",
                "runtime_parameters": {
                    "s3_key": f"s3://{os.getenv('S3_BUCKET')}/{os.getenv('S3_DATA_PATH')}"
                }
            }
        )
        if not result["success"]:
            raise ValueError(f"Validation failed: {result['run_results']}")

    validate_s3_data()

dag = s3_data_quality_dag()