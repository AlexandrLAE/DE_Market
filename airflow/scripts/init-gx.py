from great_expectations.data_context import FileDataContext
from great_expectations.core.batch import RuntimeBatchRequest
import os

def configure_gx():
    context = FileDataContext.create(project_root_dir="/opt/airflow/gx")
    
    # 1. Настройка S3 Datasource
    if "s3_datasource" not in context.datasources:
        context.sources.add_pandas_s3(
            name="s3_datasource",
            bucket=os.getenv("S3_BUCKET"),
            boto3_options={
                "endpoint_url": os.getenv("AWS_ENDPOINT_URL")
            }
        )
    
    # 2. Создание Expectation Suite
    if not context.expectations_store.has_key("basic_suite"):
        suite = context.add_expectation_suite("basic_suite")
        
        # Пример проверок
        suite.expect_column_values_to_not_be_null(column="email")
        suite.expect_column_values_to_match_regex(
            column="phone",
            regex=r"^\+?[1-9]\d{1,14}$"
        )
        context.save_expectation_suite(suite)
    
    # 3. Создание Checkpoint
    if not context.checkpoints_store.has_key("daily_validation"):
        checkpoint_config = {
            "name": "daily_validation",
            "config_version": 1,
            "validations": [{
                "batch_request": {
                    "datasource_name": "s3_datasource",
                    "data_connector_name": "default_inferred_data_connector",
                    "data_asset_name": os.getenv("S3_DATA_PATH"),
                },
                "expectation_suite_name": "basic_suite"
            }],
            "action_list": [
                {
                    "name": "store_validation_result",
                    "action": {"class_name": "StoreValidationResultAction"}
                },
                {
                    "name": "slack_notification",
                    "action": {
                        "class_name": "SlackNotificationAction",
                        "slack_webhook": os.getenv("SLACK_WEBHOOK"),
                        "notify_on": "all"
                    }
                }
            ]
        }
        context.add_checkpoint(**checkpoint_config)

if __name__ == "__main__":
    configure_gx()