import logging
import time

from app.common.config import BASE_DIR
from app.common.logger import setup_logging
from app.ingestion.client import TwelveDataClient
from app.ingestion.historical_loader import load_historical_data
from app.processing.parquet_writer import write_to_parquet


logger = logging.getLogger(__name__)


SYMBOLS = ["AAPL", "MSFT", "NVDA"]

INTERVAL = "1day"

OUTPUTSIZE = 100


def run_pipeline(
    symbols: list[str],
    interval: str,
    outputsize: int
) -> None:

    logger.info(
        "Запуск pipeline: symbols=%s, interval=%s, outputsize=%s",
        symbols,
        interval,
        outputsize
    )

    pipeline_start = time.perf_counter()

    client = TwelveDataClient()

    try:
        for symbol in symbols:

            symbol_start = time.perf_counter()

            logger.info(
                "Начинаем загрузку: symbol=%s",
                symbol
            )

            try:
                # Загружаем котировки
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

                # Формируем путь к файлу
                file_path = (
                    BASE_DIR
                    / "data"
                    / "processed"
                    / f"{symbol}_{interval}.parquet"
                )

                # Сохраняем данные
                write_to_parquet(
                    records=records,
                    file_path=file_path
                )

            except Exception:
                logger.exception(
                    "Ошибка обработки инструмента: symbol=%s",
                    symbol
                )
                raise

            duration = time.perf_counter() - symbol_start

            logger.info(
                "Загрузка завершена: symbol=%s, duration=%.2f sec",
                symbol,
                duration
            )

    finally:
        client.close()

        logger.info("HTTP-сессия закрыта")

    total_duration = time.perf_counter() - pipeline_start

    logger.info(
        "Pipeline успешно завершён: duration=%.2f sec",
        total_duration
    )


if __name__ == "__main__":

    setup_logging()

    run_pipeline(
        symbols=SYMBOLS,
        interval=INTERVAL,
        outputsize=OUTPUTSIZE
    )