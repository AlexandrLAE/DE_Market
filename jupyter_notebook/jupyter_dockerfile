FROM quay.io/jupyter/datascience-notebook:2025-03-14


COPY requirements.txt /requirements.txt

USER root

RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r /requirements.txt

RUN apt update && apt install -y openjdk-17-jdk