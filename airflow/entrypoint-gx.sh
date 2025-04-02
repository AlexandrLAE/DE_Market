#!/bin/bash

# Проверка инициализации GX
if [ ! -f "/opt/airflow/gx/great_expectations.yml" ]; then
    echo "Initializing Great Expectations..."
    
    # Инициализация с возможностью загрузки из S3
    if [ -n "${GX_CONFIG_S3_URI}" ]; then
        echo "Downloading GX config from S3..."
        aws s3 sync "${GX_CONFIG_S3_URI}" /opt/airflow/gx
    else
        great_expectations init --directory /opt/airflow/gx
    fi

    # Запуск Python-скрипта настройки
    python /opt/airflow/scripts/init-gx.py
fi

# Стандартный запуск Airflow
exec airflow "$@"