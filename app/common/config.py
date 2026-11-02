import os
from pathlib import Path

from dotenv import load_dotenv


# Определяем корневую директорию проекта
BASE_DIR = Path(__file__).resolve().parents[2]

# Загружаем переменные из .env
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

# Настройки API
API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://api.twelvedata.com"
).rstrip("/")


# Проверяем наличие API-ключа
if not API_KEY:
    raise ValueError("API_KEY не найден в файле .env")