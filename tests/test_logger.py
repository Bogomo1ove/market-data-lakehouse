import logging

from app.common.logger import setup_logging


def test_logging_message(caplog):

    setup_logging()

    logger = logging.getLogger("test_logger")

    with caplog.at_level(logging.INFO):

        logger.info("Тестовое сообщение")

    assert "Тестовое сообщение" in caplog.text