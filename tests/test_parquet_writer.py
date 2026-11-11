import pytest
import polars as pl
from datetime import date
from unittest.mock import Mock
from app.processing import parquet_writer
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

def test_write_to_parquet_merge(tmp_path):

    file_path = tmp_path / "AAPL_1day.parquet"

    old_records = [
        {
            "symbol": "AAPL",
            "datetime": "2026-10-28",
            "open": "270",
            "high": "275",
            "low": "268",
            "close": "272",
            "volume": "1000"
        },
        {
            "symbol": "AAPL",
            "datetime": "2026-10-29",
            "open": "272",
            "high": "276",
            "low": "270",
            "close": "274",
            "volume": "1100"
        }
    ]

    new_records = [
        {
            "symbol": "AAPL",
            "datetime": "2026-10-29",
            "open": "272",
            "high": "276",
            "low": "270",
            "close": "275",
            "volume": "1100"
        },
        {
            "symbol": "AAPL",
            "datetime": "2026-10-30",
            "open": "275",
            "high": "280",
            "low": "274",
            "close": "278",
            "volume": "1200"
        }
    ]

    # Первая загрузка
    write_to_parquet(old_records, file_path)

    # Вторая загрузка
    write_to_parquet(new_records, file_path)

    # Читаем результат
    df = pl.read_parquet(file_path)

    # Должно быть 3 уникальные записи
    assert df.height == 3

    # Старая запись должна сохраниться
    assert date(2026, 10, 28) in df["datetime"].to_list()

    # Исправленная цена должна заменить старую
    updated = df.filter(
        pl.col("datetime") == date(2026, 10, 29)
    )

    assert updated["close"][0] == 275.0

def test_write_to_parquet_idempotent(tmp_path):

    file_path = tmp_path / "AAPL_1day.parquet"

    records = [
        {
            "symbol": "AAPL",
            "datetime": "2026-10-30",
            "open": "270",
            "high": "275",
            "low": "268",
            "close": "272",
            "volume": "1000"
        }
    ]

    # Запускаем запись три раза
    write_to_parquet(records, file_path)
    write_to_parquet(records, file_path)
    write_to_parquet(records, file_path)

    df = pl.read_parquet(file_path)

    # Несмотря на три запуска, запись одна
    assert df.height == 1

    assert df["symbol"][0] == "AAPL"

    assert df["close"][0] == 272.0

def test_write_to_parquet_atomic_failure(
    tmp_path,
    monkeypatch
):

    file_path = tmp_path / "AAPL_1day.parquet"

    old_records = [
        {
            "symbol": "AAPL",
            "datetime": "2026-10-30",
            "open": "270",
            "high": "275",
            "low": "268",
            "close": "272",
            "volume": "1000"
        }
    ]

    new_records = [
        {
            "symbol": "AAPL",
            "datetime": "2026-11-02",
            "open": "280",
            "high": "285",
            "low": "278",
            "close": "282",
            "volume": "1200"
        }
    ]

    # Создаём исходный файл
    write_to_parquet(old_records, file_path)

    # Имитируем ошибку атомарной замены
    mock_replace = Mock(
        side_effect=OSError("Disk error")
    )

    monkeypatch.setattr(
        parquet_writer.os,
        "replace",
        mock_replace
    )

    # Ожидаем ошибку
    with pytest.raises(OSError, match="Disk error"):

        write_to_parquet(new_records, file_path)

    # Проверяем, что исходный файл сохранился
    df = pl.read_parquet(file_path)

    assert df.height == 1

    assert df["close"][0] == 272.0

    # Проверяем очистку временного файла
    assert list(tmp_path.glob(".AAPL_1day.*.tmp")) == []