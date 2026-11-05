from unittest.mock import Mock

from app.ingestion.historical_loader import load_historical_data


def test_load_historical_data():

    # Создаём поддельный API-клиент
    mock_client = Mock()

    # Настраиваем ответ клиента
    mock_client.get_time_series.return_value = {
        "status": "ok",
        "values": [
            {
                "datetime": "2026-10-30",
                "open": "270.00",
                "high": "275.00",
                "low": "268.00",
                "close": "272.00",
                "volume": "45000000"
            }
        ]
    }

    # Вызываем тестируемую функцию
    records = load_historical_data(
        client=mock_client,
        symbol="AAPL",
        interval="1day",
        outputsize=1
    )

    # Проверяем результат
    assert len(records) == 1

    assert records[0]["symbol"] == "AAPL"

    assert records[0]["close"] == "272.00"

    # Проверяем вызов клиента
    mock_client.get_time_series.assert_called_once_with(
        symbol="AAPL",
        interval="1day",
        outputsize=1
    )


import pytest


def test_load_historical_data_invalid_response():

    mock_client = Mock()

    # API вернул неожиданный JSON
    mock_client.get_time_series.return_value = {
        "status": "ok"
    }

    with pytest.raises(ValueError):
        load_historical_data(
            client=mock_client,
            symbol="AAPL"
        )