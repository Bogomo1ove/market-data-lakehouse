from app.common.config import BASE_DIR
from app.ingestion.client import TwelveDataClient
from app.ingestion.historical_loader import load_historical_data
from app.processing.parquet_writer import write_to_parquet


SYMBOLS = ["AAPL", "MSFT", "NVDA"]

INTERVAL = "1day"

OUTPUTSIZE = 100


def run_pipeline(
    symbols: list[str],
    interval: str,
    outputsize: int
) -> None:

    client = TwelveDataClient()

    try:
        for symbol in symbols:

            print(f"\nНачинаем загрузку: {symbol}")

            # Получаем исторические данные
            records = load_historical_data(
                client=client,
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )

            print(f"Получено записей: {len(records)}")

            # Формируем путь для сохранения
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

            print(f"Загрузка {symbol} завершена")

    finally:
        client.close()


if __name__ == "__main__":
    run_pipeline(
        symbols=SYMBOLS,
        interval=INTERVAL,
        outputsize=OUTPUTSIZE
    )