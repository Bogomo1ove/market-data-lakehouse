import logging
import time

import polars as pl
import requests

from app.common.config import BASE_DIR
from app.common.logger import setup_logging
from app.ingestion.client import (
    TwelveDataClient,
    TwelveDataAPIError
)
from app.ingestion.historical_loader import load_historical_data
from app.processing.parquet_writer import write_to_parquet


logger = logging.getLogger(__name__)


SYMBOLS = ["AAPL", "MSFT", "NVDA"]
INTERVAL = "1day"
OUTPUTSIZE = 100


class PipelineExecutionError(Exception):
    """Ошибка частичного или полного выполнения pipeline."""


def run_pipeline(
    symbols: list[str],
    interval: str,
    outputsize: int
) -> None:

    # Проверяем входные данные
    if not symbols:
        raise ValueError("Список инструментов не должен быть пустым")

    # Засекаем время выполнения
    pipeline_start = time.perf_counter()

    # Создаём списки успешных и неудачных загрузок
    successful_symbols = []
    failed_symbols = []

    logger.info(
        "Запуск pipeline: symbols=%s, interval=%s, outputsize=%s",
        symbols,
        interval,
        outputsize
    )

    # Создаём HTTP-клиент с поддержкой Retry
    client = TwelveDataClient(
        timeout=10,
        max_retries=2,
        backoff_factor=1.0,
        max_retry_delay=30.0
    )

    try:

        # Последовательно обрабатываем инструменты
        for symbol in symbols:

            symbol_start = time.perf_counter()

            logger.info(
                "Начинаем загрузку: symbol=%s",
                symbol
            )

            try:

                # Получаем исторические данные
                records = load_historical_data(
                    client=client,
                    symbol=symbol,
                    interval=interval,
                    outputsize=outputsize
                )

                logger.info(
                    "Получено записей: symbol=%s, count=%s",
                    symbol,
                    len(records)
                )

                # Формируем путь для сохранения
                file_path = (
                    BASE_DIR
                    / "data"
                    / "processed"
                    / f"{symbol}_{interval}.parquet"
                )

                # Сохраняем данные в Parquet
                write_to_parquet(
                    records=records,
                    file_path=file_path
                )

            # Обрабатываем ошибки отдельного инструмента
            except (
                requests.RequestException,
                TwelveDataAPIError,
                ValueError,
                pl.exceptions.PolarsError,
                OSError
            ):

                logger.exception(
                    "Ошибка обработки инструмента: symbol=%s",
                    symbol
                )

                failed_symbols.append(symbol)

                # Продолжаем загрузку остальных инструментов
                continue

            # Если ошибок не было, отмечаем успех
            successful_symbols.append(symbol)

            duration = time.perf_counter() - symbol_start

            logger.info(
                "Загрузка завершена: symbol=%s, duration=%.2f sec",
                symbol,
                duration
            )

    # Закрываем HTTP-сессию
    finally:

        client.close()

        logger.info("HTTP-сессия закрыта")

    # Рассчитываем общее время выполнения
    total_duration = time.perf_counter() - pipeline_start

    logger.info(
        "Результат pipeline: successful=%s, failed=%s, duration=%.2f sec",
        successful_symbols,
        failed_symbols,
        total_duration
    )

    # Проверяем, были ли неудачные загрузки
    if failed_symbols:

        raise PipelineExecutionError(
            f"Не удалось обработать инструменты: {failed_symbols}"
        )

    logger.info("Pipeline успешно завершён")


if __name__ == "__main__":

    setup_logging()

    run_pipeline(
        symbols=SYMBOLS,
        interval=INTERVAL,
        outputsize=OUTPUTSIZE
    )