import hashlib
from io import StringIO

import pandas as pd
import requests
import yfinance as yf

from qtools.data.cache import read_parquet, write_parquet

_COLS = ["date", "symbol", "open", "high", "low", "close", "volume"]
_UA = {"User-Agent": "Mozilla/5.0"}


def _universe_key(symbols: list[str]) -> str:
    return hashlib.md5("_".join(sorted(symbols)).encode()).hexdigest()[:10]


def _to_long(raw: pd.DataFrame, fallback_symbol: str) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        frames = []
        for ticker in raw.columns.get_level_values("Ticker").unique():
            sub = raw.xs(ticker, level="Ticker", axis=1).copy()
            sub["symbol"] = ticker
            frames.append(sub.reset_index())
        df = pd.concat(frames, ignore_index=True)
    else:
        df = raw.copy().reset_index()
        df["symbol"] = fallback_symbol

    df.columns = [c.lower() for c in df.columns]
    return df[_COLS]


def get_us_prices(
    symbols: list[str],
    start: str,
    end: str,
    adjust: bool = True,
    chunk_size: int = 50,
) -> pd.DataFrame:
    cache_key = f"{_universe_key(symbols)}_{start}_{end}_adj{adjust}"
    cached = read_parquet("us_prices", cache_key)
    if cached is not None:
        return cached

    frames = []
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i : i + chunk_size]
        raw = yf.download(
            chunk,
            start=start,
            end=end,
            auto_adjust=adjust,
            progress=False,
            threads=True,
        )
        if raw.empty:
            continue
        frames.append(_to_long(raw, fallback_symbol=chunk[0]))

    if not frames:
        return pd.DataFrame(columns=_COLS)

    df = (
        pd.concat(frames, ignore_index=True)
        .dropna(subset=["close"])
        .sort_values(["symbol", "date"])
        .reset_index(drop=True)
    )

    write_parquet("us_prices", cache_key, df)
    return df


def get_sp500_constituents(as_of: str | None = None) -> list[str]:
    """Current S&P 500 tickers from Wikipedia. `as_of` is ignored (always current)."""
    r = requests.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers=_UA,
        timeout=15,
    )
    r.raise_for_status()
    tables = pd.read_html(StringIO(r.text))
    return sorted(tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist())
