from airflow.sensors.base import BaseSensorOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from typing import Any, Optional
from airflow.utils.context import Context
import time

class S3ConnectionSensor(BaseSensorOperator):
    """
    Сенсор для проверки соединения с S3.

    :param aws_conn_id: ID соединения AWS в Airflow
    :param bucket_name: Имя бакета для проверки (опционально)
    :param max_retries: Максимальное количество попыток проверки
    :param retry_delay: Задержка между попытками в секундах
    """

    template_fields = ("aws_conn_id", "bucket_name")

    def __init__(
        self,
        *,
        aws_conn_id: str = "aws_default",
        bucket_name: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 60,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.aws_conn_id = aws_conn_id
        self.bucket_name = bucket_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.hook = None

    def poke(self, context: Context) -> bool:
        """Основной метод проверки соединения"""
        try:
            self.log.info("Начало проверки соединения с S3")
            # Инициализация хука S3
            self.hook = S3Hook(aws_conn_id=self.aws_conn_id)
            
            # Если указано имя бакета, проверяем доступ к нему
            if self.bucket_name:
                self.log.info("Проверка доступа к бакету: %s", self.bucket_name)
                if not self.hook.check_for_bucket(self.bucket_name):
                    self.log.warning("Бакет %s не найден или нет доступа", self.bucket_name)
                    return False
                self.log.info("Успешное соединение с бакетом %s", self.bucket_name)
                
            else:
                # Простая проверка соединения без указания бакета
                self.log.info("Проверка соединения с S3")
                self.hook.get_conn()
                self.log.info("Успешное соединение с S3")


            return True

        except Exception as e:
            self.log.error("Ошибка соединения с S3: %s", str(e))
            if self.max_retries > 0:
                self.max_retries -= 1
                self.log.info("Повторная попытка через %s секунд...", self.retry_delay)
                time.sleep(self.retry_delay)
            return False

