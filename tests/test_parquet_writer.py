import pandas as pd

from app.processing.parquet_writer import write_to_parquet


def test_write_to_parquet(tmp_path):

    # Подготавливаем тестовые данные
    records = [
        {
            "symbol": "AAPL",
            "datetime": "2026-10-30",
            "open": "270.00",
            "high": "275.00",
            "low": "268.00",
            "close": "272.00",
            "volume": "45000000"
        }
    ]

    # Путь к временному файлу
    file_path = tmp_path / "test_prices.parquet"

    # Сохраняем данные
    write_to_parquet(
        records=records,
        file_path=file_path
    )

    # Проверяем существование файла
    assert file_path.exists()

    # Читаем сохранённый Parquet
    df = pd.read_parquet(file_path)

    # Проверяем количество строк
    assert len(df) == 1

    # Проверяем значения
    assert df.iloc[0]["symbol"] == "AAPL"

    assert df.iloc[0]["close"] == 272.00

    # Проверяем типы данных
    assert pd.api.types.is_float_dtype(df["close"])

    assert pd.api.types.is_integer_dtype(df["volume"])

    assert pd.api.types.is_datetime64_any_dtype(df["datetime"])


import pytest


def test_write_to_parquet_empty_records(tmp_path):

    file_path = tmp_path / "empty.parquet"

    with pytest.raises(
        ValueError,
        match="Нет данных для сохранения"
    ):
        write_to_parquet(
            records=[],
            file_path=file_path
        )

    assert not file_path.exists()