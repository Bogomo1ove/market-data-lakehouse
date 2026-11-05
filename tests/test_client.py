from unittest.mock import Mock

import pytest
import requests

from app.common.config import API_KEY, API_BASE_URL
from app.ingestion.client import (
    TwelveDataClient,
    TwelveDataAPIError
)


@pytest.fixture
def client():
    api_client = TwelveDataClient(timeout=3)

    yield api_client

    api_client.close()

def test_get_time_series_success(client, monkeypatch):

    # Подготавливаем ответ API
    mock_response = Mock()

    mock_response.json.return_value = {
        "status": "ok",
        "meta": {
            "symbol": "AAPL"
        },
        "values": [
            {
                "datetime": "2026-10-30",
                "close": "272.00"
            }
        ]
    }

    # Подменяем настоящий HTTP-запрос
    mock_get = Mock(return_value=mock_response)

    monkeypatch.setattr(
        client.session,
        "get",
        mock_get
    )

    # Вызываем метод клиента
    result = client.get_time_series(
        symbol="AAPL",
        interval="1day",
        outputsize=1
    )

    # Проверяем результат
    assert result["status"] == "ok"

    assert result["meta"]["symbol"] == "AAPL"

    assert len(result["values"]) == 1

    # Проверяем параметры HTTP-запроса
    mock_get.assert_called_once_with(
        f"{API_BASE_URL}/time_series",
        params={
            "symbol": "AAPL",
            "interval": "1day",
            "outputsize": 1
        },
        timeout=3
    )

    # Проверяем выполнение HTTP-проверки
    mock_response.raise_for_status.assert_called_once_with()

def test_client_authorization(client):

    assert client.session.headers["Authorization"] == (
        f"apikey {API_KEY}"
    )

def test_get_time_series_http_error(client, monkeypatch):

    mock_response = Mock()

    # Имитируем HTTP-ошибку
    mock_response.raise_for_status.side_effect = (
        requests.HTTPError("503 Service Unavailable")
    )

    mock_get = Mock(return_value=mock_response)

    monkeypatch.setattr(
        client.session,
        "get",
        mock_get
    )

    # Проверяем возникновение исключения
    with pytest.raises(
        requests.HTTPError,
        match="503 Service Unavailable"
    ):
        client.get_time_series(
            symbol="AAPL"
        )

    # JSON не должен обрабатываться после HTTP-ошибки
    mock_response.json.assert_not_called()

def test_get_time_series_api_error(client, monkeypatch):

    mock_response = Mock()

    mock_response.json.return_value = {
        "status": "error",
        "code": 400,
        "message": "Invalid symbol"
    }

    mock_get = Mock(return_value=mock_response)

    monkeypatch.setattr(
        client.session,
        "get",
        mock_get
    )

    with pytest.raises(
        TwelveDataAPIError,
        match="Invalid symbol"
    ):
        client.get_time_series(
            symbol="INVALID"
        )

def test_get_time_series_timeout(client, monkeypatch):

    mock_get = Mock(
        side_effect=requests.Timeout(
            "Request timed out"
        )
    )

    monkeypatch.setattr(
        client.session,
        "get",
        mock_get
    )

    with pytest.raises(
        requests.Timeout,
        match="Request timed out"
    ):
        client.get_time_series(
            symbol="AAPL"
        )