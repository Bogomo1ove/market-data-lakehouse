import requests

from app.common.config import API_KEY, API_BASE_URL


class TwelveDataAPIError(Exception):
    """Ошибка, возвращаемая API Twelve Data."""


class TwelveDataClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

        # Создаём сессию для HTTP-запросов
        self.session = requests.Session()

        # Передаём API-ключ через HTTP-заголовок
        self.session.headers.update({
            "Authorization": f"apikey {API_KEY}"
        })

    def _get(self, endpoint: str, params: dict) -> dict:
        """
        Выполняет GET-запрос к Twelve Data
        и возвращает ответ в формате JSON.
        """

        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout
        )

        # Проверяем HTTP-ошибки
        response.raise_for_status()

        data = response.json()

        # Проверяем ошибки непосредственно от Twelve Data
        if data.get("status") == "error":
            raise TwelveDataAPIError(
                f"API error {data.get('code')}: {data.get('message')}"
            )

        return data

    def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 5
    ) -> dict:
        """
        Получает исторические котировки инструмента.
        """

        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }

        return self._get("time_series", params)

    def close(self):
        """Закрывает HTTP-сессию."""
        self.session.close()