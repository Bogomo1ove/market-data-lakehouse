from unittest.mock import Mock

import pytest
import requests

from app.ingestion import pipeline


def test_pipeline_partial_failure(monkeypatch, tmp_path):

    mock_client = Mock()

    monkeypatch.setattr(
        pipeline,
        "TwelveDataClient",
        Mock(return_value=mock_client)
    )

    monkeypatch.setattr(
        pipeline,
        "BASE_DIR",
        tmp_path
    )

    def mock_load_data(client, symbol, interval, outputsize):

        if symbol == "MSFT":
            raise requests.Timeout("API timeout")

        return [
            {
                "symbol": symbol,
                "datetime": "2026-10-30",
                "close": "272.00"
            }
        ]

    monkeypatch.setattr(
        pipeline,
        "load_historical_data",
        mock_load_data
    )

    mock_writer = Mock()

    monkeypatch.setattr(
        pipeline,
        "write_to_parquet",
        mock_writer
    )

    with pytest.raises(
        pipeline.PipelineExecutionError,
        match="MSFT"
    ):
        pipeline.run_pipeline(
            symbols=["AAPL", "MSFT", "NVDA"],
            interval="1day",
            outputsize=100
        )

    assert mock_writer.call_count == 2

    saved_files = [
        call.kwargs["file_path"].name
        for call in mock_writer.call_args_list
    ]

    assert saved_files == [
        "AAPL_1day.parquet",
        "NVDA_1day.parquet"
    ]

    mock_client.close.assert_called_once()


def test_pipeline_empty_symbols(monkeypatch):

    mock_client_factory = Mock()

    monkeypatch.setattr(
        pipeline,
        "TwelveDataClient",
        mock_client_factory
    )

    with pytest.raises(
        ValueError,
        match="Список инструментов не должен быть пустым"
    ):
        pipeline.run_pipeline(
            symbols=[],
            interval="1day",
            outputsize=100
        )

    mock_client_factory.assert_not_called()