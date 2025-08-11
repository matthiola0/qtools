import pandas as pd
import yfinance as yf

from qtools.data._util import require_ohlcv_columns, ticker_level_name, universe_key
from qtools.data.cache import read_parquet, write_parquet

_COLS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def _to_long(raw: pd.DataFrame, fallback_symbol: str) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        level = ticker_level_name(raw.columns, source="get_tw_prices")
        frames = []
        for yf_sym in raw.columns.get_level_values(level).unique():
            sub = raw.xs(yf_sym, level=level, axis=1).copy()
            sub["symbol"] = yf_sym.replace(".TW", "")
            frames.append(sub.reset_index())
        df = pd.concat(frames, ignore_index=True)
    else:
        df = raw.copy().reset_index()
        df["symbol"] = fallback_symbol.replace(".TW", "")

    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={"datetime": "date"})  # intraday uses "Datetime"
    require_ohlcv_columns(df, source="get_tw_prices")
    return df[_COLS]


def get_tw_prices(
    symbols: list[str],
    start: str,
    end: str,
    adjust: bool = True,
    interval: str = "1d",
    chunk_size: int = 50,
) -> pd.DataFrame:
    """Download Taiwan equity bars via Yahoo Finance `.TW` tickers.

    See `get_us_prices` for supported intervals and Yahoo history restrictions.
    """
    cache_key = f"{universe_key(symbols)}_{start}_{end}_adj{adjust}"
    if interval != "1d":
        cache_key += f"_{interval}"
    cached = read_parquet("tw_prices", cache_key)
    if cached is not None:
        return cached

    yf_tickers = [f"{s}.TW" for s in symbols]

    frames = []
    for i in range(0, len(yf_tickers), chunk_size):
        chunk = yf_tickers[i : i + chunk_size]
        raw = yf.download(
            chunk,
            start=start,
            end=end,
            interval=interval,
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

    write_parquet("tw_prices", cache_key, df)
    return df


# 0050 constituents snapshot (manually updated).
# For exact current list: https://www.yuantaetfs.com/product/detail/0050/ratio
_TW50_TICKERS = [
    "2330", "2317", "2454", "2308", "2382", "2881", "2891", "2303", "3711", "2882",
    "2886", "1301", "2412", "3034", "2884", "1303", "5880", "2357", "3231", "2002",
    "1216", "2885", "6669", "3037", "2892", "4938", "5876", "2207", "1101", "2345",
    "3661", "2880", "4904", "6505", "2887", "3045", "2801", "1326", "2883", "6415",
    "2379", "5871", "2912", "9910", "1590", "8046", "2603", "3017", "2395", "6409",
]


def get_tw50_constituents(as_of: str | None = None) -> list[str]:
    return _TW50_TICKERS.copy()
