from pathlib import Path
import logging
import polars as pl


logger = logging.getLogger(__name__)

def write_to_parquet(
    records: list[dict],
    file_path: str | Path
) -> None:
    """
    Преобразует исторические дневные котировки
    и сохраняет их в формате Parquet.
    """

    if not records:
        raise ValueError("Нет данных для сохранения")

    # Создаём DataFrame
    df = pl.from_dicts(records)

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

    # Преобразуем типы данных
    df = df.with_columns(
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

    # Сортируем по дате
    df = df.sort("datetime")

    # Подготавливаем путь
    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Сохраняем Parquet
    df.write_parquet(
        file_path,
        compression="zstd"
    )

    logger.info(
        "Parquet сохранён: path=%s, rows=%s",
        file_path,
        df.height
    )