from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Закрытые ПИФы (ЗПИФы); всё остальное в каталоге считается открытым.
CLOSED_FUNDS = {
    "Фонд Современный Арендный бизнес 2",
    "Фонд Современный 6",
}

SRC_COLUMNS = {
    "Дата": "date",
    "Пай (₽)": "price",
    "СЧА (₽)": "nav",
    "Выплаченный (зарезервированный) по инвестиционным паям инвестиционный доход (₽)": "income",
}


def fund_name(path: Path) -> str:
    """Имя фонда — часть имени файла до даты выгрузки."""
    return path.stem.split("_")[0].strip()


def load_one(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, decimal=",", thousands=" ")
    df = df.rename(columns=SRC_COLUMNS)[list(SRC_COLUMNS.values())]
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    name = fund_name(path)
    df.insert(1, "fund", name)
    df.insert(2, "fund_type", "closed" if name in CLOSED_FUNDS else "open")
    return df


def merge(src: Path, out: Path) -> pd.DataFrame:
    files = sorted(src.glob("*.xlsx"))
    if not files:
        raise SystemExit(f"Не найдено ни одного .xlsx в {src}")
    frames = [load_one(p) for p in files]
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values(["fund_type", "fund", "date"]).reset_index(drop=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out, index=False, encoding="utf-8")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/funds.csv"))
    args = parser.parse_args()

    merged = merge(args.src, args.out)
    n_funds = merged["fund"].nunique()
    print(f"Записано {len(merged):,} строк по {n_funds} фондам → {args.out}")
    print(merged.groupby("fund_type")["fund"].nunique().to_string())


if __name__ == "__main__":
    main()
