import logging
import time

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from app.common.config import API_KEY, API_BASE_URL


logger = logging.getLogger(__name__)

RETRYABLE_STATUSES = {500, 502, 503, 504}


class TwelveDataAPIError(Exception):
    """Ошибка, возвращаемая API Twelve Data."""


class TwelveDataClient:

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 0,
        backoff_factor: float = 1.0,
        max_retry_delay: float = 30.0
    ):
        if max_retries < 0 or backoff_factor < 0 or max_retry_delay < 0:
            raise ValueError(
                "Параметры повторных попыток не могут быть отрицательными"
            )

        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_retry_delay = max_retry_delay

        self.session = requests.Session()

        self.session.headers.update({
            "Authorization": f"apikey {API_KEY}"
        })

    @staticmethod
    def _retry_after_seconds(response: requests.Response) -> float | None:
        """Читает Retry-After в секундах или формате HTTP-даты."""

        value = response.headers.get("Retry-After")

        if not isinstance(value, str):
            return None

        try:
            seconds = int(value)

        except ValueError:
            try:
                retry_time = parsedate_to_datetime(value)
            except (TypeError, ValueError, IndexError, OverflowError):
                return None

            if retry_time.tzinfo is None:
                return None

            seconds = max(
                0.0,
                (retry_time - datetime.now(timezone.utc)).total_seconds()
            )

        return float(seconds) if seconds >= 0 else None

    def _retry_delay(
        self,
        attempt: int,
        response: requests.Response | None = None,
        require_header: bool = False
    ) -> float | None:
        """Рассчитывает задержку перед повтором."""

        retry_after = (
            self._retry_after_seconds(response)
            if response is not None
            else None
        )

        if retry_after is not None:
            if retry_after <= self.max_retry_delay:
                return retry_after

            return None

        if require_header:
            return None

        return min(
            self.backoff_factor * 2 ** attempt,
            self.max_retry_delay
        )

    def _get(self, endpoint: str, params: dict) -> dict:
        """Выполняет GET-запрос с ограниченными повторами."""

        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries + 1):

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

            except (requests.Timeout, requests.ConnectionError) as exc:

                if attempt == self.max_retries:
                    raise

                delay = self._retry_delay(attempt)

                logger.warning(
                    "Сетевая ошибка %s; повтор %s/%s через %.1f сек",
                    type(exc).__name__,
                    attempt + 1,
                    self.max_retries,
                    delay
                )

                time.sleep(delay)
                continue

            # Обработка временных HTTP-ошибок
            status = response.status_code

            if (
                status in RETRYABLE_STATUSES | {429}
                and attempt < self.max_retries
            ):
                delay = self._retry_delay(
                    attempt,
                    response,
                    require_header=(status == 429)
                )

                if delay is not None:
                    logger.warning(
                        "HTTP %s; повтор %s/%s через %.1f сек",
                        status,
                        attempt + 1,
                        self.max_retries,
                        delay
                    )

                    time.sleep(delay)
                    continue

            response.raise_for_status()

            data = response.json()

            # Ошибка внутри JSON-ответа Twelve Data
            if data.get("status") == "error":

                code = str(data.get("code"))

                if (
                    code in {"429", "500", "502", "503", "504"}
                    and attempt < self.max_retries
                ):
                    delay = self._retry_delay(
                        attempt,
                        response,
                        require_header=(code == "429")
                    )

                    if delay is not None:
                        logger.warning(
                            "Ошибка API %s; повтор %s/%s через %.1f сек",
                            code,
                            attempt + 1,
                            self.max_retries,
                            delay
                        )

                        time.sleep(delay)
                        continue

                raise TwelveDataAPIError(
                    f"API error {data.get('code')}: {data.get('message')}"
                )

            return data

        raise RuntimeError("Неожиданное завершение цикла запросов")

    def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 5
    ) -> dict:

        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }

        return self._get("time_series", params)

    def close(self):
        self.session.close()