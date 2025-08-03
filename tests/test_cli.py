from argparse import Namespace
from unittest.mock import patch

import pandas as pd
import pytest

from qtools.cli import build_parser, cmd_fetch


# ---------- argument parsing ----------

def test_fetch_parses_basic():
    args = build_parser().parse_args([
        "fetch", "us", "AAPL", "--start", "2024-01-01", "--end", "2024-06-30",
    ])
    assert args.cmd == "fetch"
    assert args.market == "us"
    assert args.symbols == ["AAPL"]
    assert args.start == "2024-01-01"
    assert args.end == "2024-06-30"
    assert args.interval == "1d"  # default
    assert args.output is None


def test_fetch_parses_multiple_symbols_and_interval():
    args = build_parser().parse_args([
        "fetch", "crypto", "BTC/USDT", "ETH/USDT",
        "--start", "2024-01-01", "--end", "2024-01-02",
        "--interval", "1m",
    ])
    assert args.symbols == ["BTC/USDT", "ETH/USDT"]
    assert args.interval == "1m"


def test_fetch_parses_output():
    args = build_parser().parse_args([
        "fetch", "us", "AAPL",
        "--start", "2024-01-01", "--end", "2024-06-30",
        "-o", "out.parquet",
    ])
    assert args.output == "out.parquet"


def test_universe_parses():
    args = build_parser().parse_args(["universe", "tw"])
    assert args.cmd == "universe"
    assert args.market == "tw"


def test_invalid_market_exits():
    with pytest.raises(SystemExit):
        build_parser().parse_args([
            "fetch", "bogus", "AAPL", "--start", "2024-01-01", "--end", "2024-06-30",
        ])


def test_missing_required_exits():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["fetch", "us", "AAPL"])  # no --start / --end


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0


# ---------- command dispatch (mocked loaders; no network) ----------

_SAMPLE_DF = pd.DataFrame({
    "date":   pd.to_datetime(["2024-01-02", "2024-01-03"]),
    "symbol": ["AAPL", "AAPL"],
    "open":   [100.0, 101.0],
    "high":   [101.0, 102.0],
    "low":    [99.0, 100.0],
    "close":  [100.5, 101.5],
    "volume": [1000.0, 2000.0],
})


def test_cmd_fetch_prints_when_no_output(capsys):
    args = Namespace(market="us", symbols=["AAPL"],
                     start="2024-01-01", end="2024-01-04",
                     interval="1d", output=None)
    with patch("qtools.cli._LOADERS", {"us": lambda *a, **kw: _SAMPLE_DF}):
        rc = cmd_fetch(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "2 rows" in out


def test_cmd_fetch_writes_parquet(tmp_path):
    out_file = tmp_path / "out.parquet"
    args = Namespace(market="us", symbols=["AAPL"],
                     start="2024-01-01", end="2024-01-04",
                     interval="1d", output=str(out_file))
    with patch("qtools.cli._LOADERS", {"us": lambda *a, **kw: _SAMPLE_DF}):
        rc = cmd_fetch(args)
    assert rc == 0
    assert out_file.exists()
    pd.testing.assert_frame_equal(pd.read_parquet(out_file), _SAMPLE_DF)


def test_cmd_fetch_writes_csv(tmp_path):
    out_file = tmp_path / "out.csv"
    args = Namespace(market="us", symbols=["AAPL"],
                     start="2024-01-01", end="2024-01-04",
                     interval="1d", output=str(out_file))
    with patch("qtools.cli._LOADERS", {"us": lambda *a, **kw: _SAMPLE_DF}):
        rc = cmd_fetch(args)
    assert rc == 0
    assert out_file.exists()
    # CSV round-trip may not preserve dtypes exactly; just check row count
    assert len(pd.read_csv(out_file)) == 2


def test_cmd_fetch_returns_1_on_empty():
    empty = pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
    args = Namespace(market="us", symbols=["NOPE"],
                     start="2024-01-01", end="2024-01-04",
                     interval="1d", output=None)
    with patch("qtools.cli._LOADERS", {"us": lambda *a, **kw: empty}):
        assert cmd_fetch(args) == 1
