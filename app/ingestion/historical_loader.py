from app.ingestion.client import TwelveDataClient


def load_historical_data(
    client: TwelveDataClient,
    symbol: str,
    interval: str = "1day",
    outputsize: int = 100
) -> list[dict]:
    """
    Загружает исторические котировки инструмента.

    Возвращает список словарей с котировками.
    """

    response = client.get_time_series(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize
    )

    values = response.get("values")

    if not isinstance(values, list):
        raise ValueError(
            f"Некорректный ответ API для {symbol}: отсутствует список values"
        )

    records = []

    for value in values:
        record = {
            "symbol": symbol,
            **value
        }

        records.append(record)

    return records