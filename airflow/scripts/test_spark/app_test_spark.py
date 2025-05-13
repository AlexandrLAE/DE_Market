import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, year, month


def main():
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", required=True, help="Путь к входным данным")
    parser.add_argument("--output-path", required=True, help="Путь для сохранения результатов")
    parser.add_argument("--date", required=True, help="Дата обработки в формате YYYY-MM-DD")
    args = parser.parse_args()

    # Инициализация SparkSession
    spark = SparkSession.builder \
        .appName("AirflowSparkETL") \
        .getOrCreate()

    try:
        # Логирование параметров
        spark.sparkContext.setLogLevel("INFO")
        spark.logger.info(f"Starting ETL job for date: {args.date}")
        spark.logger.info(f"Input path: {args.input_path}")
        spark.logger.info(f"Output path: {args.output_path}")

        # Чтение данных (пример для CSV, может быть Parquet, JSON и т.д.)
        df = spark.read.csv(
            args.input_path,
            header=True,
            inferSchema=True
        )

        # Пример трансформаций
        processed_df = df \
            .withColumn("transaction_date", to_date(col("timestamp"))) \
            .filter(year(col("transaction_date")) == 2023) \
            .withColumn("month", month(col("transaction_date")))

        # Агрегация данных (пример)
        aggregated_df = processed_df.groupBy("month", "category") \
            .agg(
                {"amount": "sum", "transaction_id": "count"}
            ) \
            .withColumnRenamed("sum(amount)", "total_amount") \
            .withColumnRenamed("count(transaction_id)", "transaction_count")

        # Сохранение результатов
        aggregated_df.write.parquet(
            f"{args.output_path}/date={args.date}",
            mode="overwrite"
        )

        spark.logger.info("Job completed successfully!")
    except Exception as e:
        spark.logger.error(f"Job failed with error: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()