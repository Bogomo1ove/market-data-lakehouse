import logging
import os
import tempfile

from pathlib import Path

import polars as pl


logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "symbol",
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def write_to_parquet(
    records: list[dict],
    file_path: str | Path
) -> None:
    """
    Объединяет новые котировки с существующими,
    удаляет дубликаты и атомарно обновляет Parquet.
    """

    # 1. Проверяем наличие данных
    if not records:
        raise ValueError("Нет данных для сохранения")

    # 2. Создаём DataFrame
    df = pl.from_dicts(records)

    # 3. Проверяем обязательные колонки
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Отсутствуют обязательные колонки: {missing_columns}"
        )

    # 4. Преобразуем данные к единой схеме
    df = df.select(
        pl.col("symbol").cast(pl.String),
        pl.col("datetime").str.to_date(
            "%Y-%m-%d",
            strict=True
        ),
        pl.col("open").cast(pl.Float64, strict=True),
        pl.col("high").cast(pl.Float64, strict=True),
        pl.col("low").cast(pl.Float64, strict=True),
        pl.col("close").cast(pl.Float64, strict=True),
        pl.col("volume").cast(pl.Int64, strict=True)
    )

    # 5. Проверяем ключевые поля
    if df["symbol"].null_count() or df["datetime"].null_count():
        raise ValueError(
            "Поля symbol и datetime не могут содержать NULL"
        )

    # 6. Подготавливаем путь
    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 7. Если файл существует, читаем старые данные
    if file_path.exists():

        existing_df = pl.read_parquet(file_path)

        # Проверяем совместимость схем
        if existing_df.schema != df.schema:
            raise ValueError(
                "Схема существующего Parquet "
                "не совпадает со схемой новых данных"
            )

        # Объединяем старые и новые записи
        df = pl.concat(
            [existing_df, df],
            how="vertical"
        )

    # 8. Удаляем дубликаты
    df = df.unique(
        subset=["symbol", "datetime"],
        keep="last",
        maintain_order=True
    )

    # 9. Сортируем записи
    df = df.sort(
        ["symbol", "datetime"]
    )

    # 10. Создаём временный файл
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=file_path.parent,
        prefix=f".{file_path.stem}.",
        suffix=".tmp",
        delete=False
    ) as temp_file:

        temp_path = Path(temp_file.name)

    try:
        # 11. Записываем данные во временный Parquet
        df.write_parquet(
            temp_path,
            compression="zstd"
        )

        # 12. Заменяем основной файл
        os.replace(
            temp_path,
            file_path
        )

    finally:
        # Удаляем временный файл, если он остался
        temp_path.unlink(missing_ok=True)

    logger.info(
        "Parquet обновлён: path=%s, total_rows=%s",
        file_path,
        df.height
    )