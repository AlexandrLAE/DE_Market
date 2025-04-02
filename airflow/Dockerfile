FROM apache/airflow:2.10.5-python3.10

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    libpq-dev \
    gcc \
    git \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

    # Установка Spark
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PYSPARK_PYTHON=python3

COPY --from=apache/spark:3.5.0 /opt/spark /opt/spark

# Копируем скрипты инициализации GX
COPY ./entrypoint-gx.sh /entrypoint-gx.sh
COPY scripts/init-gx.py /opt/airflow/scripts/init-gx.py
RUN chmod +x /entrypoint-gx.sh

USER airflow
RUN pip install --upgrade pip setuptools --disable-pip-version-check
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
# Переопределяем точку входа
ENTRYPOINT ["/entrypoint-gx.sh"]