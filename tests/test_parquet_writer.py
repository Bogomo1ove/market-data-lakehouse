import pytest
import polars as pl

from app.processing.parquet_writer import write_to_parquet


def test_write_to_parquet(tmp_path):

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

    file_path = tmp_path / "test_prices.parquet"

    write_to_parquet(
        records=records,
        file_path=file_path
    )

    # Проверяем существование файла
    assert file_path.exists()

    # Читаем Parquet через Polars
    df = pl.read_parquet(file_path)

    # Проверяем количество строк
    assert df.height == 1

    # Проверяем значения
    assert df["symbol"][0] == "AAPL"

    assert df["close"][0] == 272.00

    # Проверяем типы
    assert df.schema["datetime"] == pl.Date

    assert df.schema["close"] == pl.Float64

    assert df.schema["volume"] == pl.Int64


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