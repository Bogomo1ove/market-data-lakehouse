from pathlib import Path

import pandas as pd


def write_to_parquet(
    records: list[dict],
    file_path: str | Path
) -> None:
    """
    Преобразует исторические котировки
    и сохраняет их в формате Parquet.
    """

    if not records:
        raise ValueError("Нет данных для сохранения")

    # Создаём DataFrame
    df = pd.DataFrame(records)

    # Проверяем обязательные колонки
    required_columns = {
        "symbol",
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Отсутствуют обязательные колонки: {missing_columns}"
        )

    # Преобразуем дату
    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="raise"
    )

    # Преобразуем цены в числовой формат
    price_columns = ["open", "high", "low", "close"]

    for column in price_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        ).astype("float64")

    # Преобразуем объём торгов в целое число
    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="raise"
    ).astype("Int64")

    # Сортируем данные
    df = df.sort_values("datetime")

    # Подготавливаем путь
    file_path = Path(file_path)

    # Создаём директории, если их нет
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Сохраняем данные
    df.to_parquet(
        file_path,
        engine="pyarrow",
        index=False
    )

    print(f"Сохранено {len(df)} записей в {file_path}")