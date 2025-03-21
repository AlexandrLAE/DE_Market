echo 'FROM apache/airflow:2.10.5

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --upgrade pip setuptools --disable-pip-version-check
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt' > Dockerfile