from datetime import datetime, timezone

import ccxt
import pandas as pd

from qtools.data.cache import read_parquet, write_parquet

_COLS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def _ts(date_str: str) -> int:
    """ISO date string → millisecond timestamp."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def get_crypto_prices(
    symbols: list[str],
    start: str,
    end: str,
    interval: str = "1d",
    exchange: str = "binance",
) -> pd.DataFrame:
    cache_key = f"{'_'.join(sorted(symbols)[:5])}_{start}_{end}_{interval}"
    cached = read_parquet("crypto_prices", cache_key)
    if cached is not None:
        return cached

    ex = getattr(ccxt, exchange)({"enableRateLimit": True})

    since = _ts(start)
    end_ms = _ts(end)

    frames = []
    for sym in symbols:
        bars = []
        cursor = since
        while cursor < end_ms:
            chunk = ex.fetch_ohlcv(sym, interval, since=cursor, limit=1000)
            if not chunk:
                break
            bars.extend(chunk)
            cursor = chunk[-1][0] + 1

        if not bars:
            continue

        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
        df["symbol"] = sym
        df = df[df["date"] < end]
        frames.append(df[_COLS])

    if not frames:
        return pd.DataFrame(columns=_COLS)

    result = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["symbol", "date"])
        .reset_index(drop=True)
    )

    write_parquet("crypto_prices", cache_key, result)
    return result


def get_top_pairs(n: int = 30, quote: str = "USDT", exchange: str = "binance") -> list[str]:
    """Top N pairs by 24h quote volume on the given exchange."""
    ex = getattr(ccxt, exchange)({"enableRateLimit": True})
    tickers = ex.fetch_tickers()

    pairs = []
    for sym, info in tickers.items():
        if sym.endswith(f"/{quote}") and info.get("quoteVolume"):
            pairs.append((sym, info["quoteVolume"]))

    pairs.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in pairs[:n]]
