"""Command-line interface for qtools.

Examples
--------
    # Daily close for two US tickers
    qtools fetch us AAPL TSLA --start 2024-01-01 --end 2024-12-31

    # 1-hour bars for TSMC (only last 730 days available from Yahoo)
    qtools fetch tw 2330 --start 2024-01-01 --end 2024-06-30 --interval 1h

    # 1-minute BTC (history not limited on Binance)
    qtools fetch crypto BTC/USDT --start 2024-04-01 --end 2024-04-02 --interval 1m

    # Save to parquet
    qtools fetch us AAPL MSFT --start 2024-01-01 --end 2024-06-30 -o out.parquet

    # List the default universes
    qtools universe us      # S&P 500
    qtools universe tw      # 0050 constituents
    qtools universe crypto  # top 30 USDT pairs by 24h volume
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qtools.data.loaders.crypto import get_crypto_prices, get_top_pairs
from qtools.data.loaders.twse import get_tw50_constituents, get_tw_prices
from qtools.data.loaders.us import get_sp500_constituents, get_us_prices

_LOADERS = {
    "us":     get_us_prices,
    "tw":     get_tw_prices,
    "crypto": get_crypto_prices,
}

_UNIVERSES = {
    "us":     get_sp500_constituents,
    "tw":     get_tw50_constituents,
    "crypto": lambda: get_top_pairs(30),
}


def cmd_fetch(args: argparse.Namespace) -> int:
    loader = _LOADERS[args.market]
    df = loader(args.symbols, start=args.start, end=args.end, interval=args.interval)

    if df.empty:
        print("No data returned.", file=sys.stderr)
        return 1

    if args.output:
        out = Path(args.output)
        if out.suffix == ".csv":
            df.to_csv(out, index=False)
        else:
            df.to_parquet(out, index=False)
        print(f"wrote {len(df):,} rows to {out}")
        return 0

    print(df.head(10).to_string(index=False))
    print(
        f"\n{len(df):,} rows  {df['symbol'].nunique()} symbols  "
        f"{df['date'].min()}  ->  {df['date'].max()}"
    )
    return 0


def cmd_universe(args: argparse.Namespace) -> int:
    tickers = _UNIVERSES[args.market]()
    print("\n".join(tickers))
    print(f"\n{len(tickers)} symbols", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qtools", description="Quant research toolkit CLI"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("fetch", help="Download price bars for given symbols.")
    pf.add_argument("market", choices=list(_LOADERS))
    pf.add_argument("symbols", nargs="+", help="One or more tickers (e.g. AAPL, 2330, BTC/USDT)")
    pf.add_argument("--start", required=True, help="YYYY-MM-DD")
    pf.add_argument("--end", required=True, help="YYYY-MM-DD")
    pf.add_argument(
        "--interval",
        default="1d",
        help="Bar interval (default: 1d). US/TW: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo. "
             "Crypto/Binance: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M.",
    )
    pf.add_argument("-o", "--output", help="Save to .parquet or .csv instead of printing.")

    pu = sub.add_parser("universe", help="List the default universe for a market.")
    pu.add_argument("market", choices=list(_UNIVERSES))

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"fetch": cmd_fetch, "universe": cmd_universe}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
