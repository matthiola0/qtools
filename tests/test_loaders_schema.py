import pandas as pd
import pytest

from qtools.data._util import require_ohlcv_columns, ticker_level_name


def test_ticker_level_name_accepts_ticker():
    cols = pd.MultiIndex.from_product(
        [["AAPL", "MSFT"], ["Open", "High", "Low", "Close", "Volume"]],
        names=["Ticker", "Price"],
    )
    assert ticker_level_name(cols, source="test") == "Ticker"


def test_ticker_level_name_accepts_aliases():
    for alias in ("Ticker/Symbol", "symbol", "Symbol"):
        cols = pd.MultiIndex.from_product(
            [["AAPL"], ["Close"]], names=[alias, "Price"]
        )
        assert ticker_level_name(cols, source="test") == alias


def test_ticker_level_name_rejects_unknown_schema():
    cols = pd.MultiIndex.from_product(
        [["AAPL"], ["Close"]], names=["Foo", "Bar"]
    )
    with pytest.raises(ValueError, match="could not find ticker level"):
        ticker_level_name(cols, source="get_us_prices")


def test_require_ohlcv_columns_passes_on_complete_frame():
    df = pd.DataFrame(
        {c: [] for c in ["date", "symbol", "open", "high", "low", "close", "volume"]}
    )
    require_ohlcv_columns(df, source="test")


def test_require_ohlcv_columns_reports_missing():
    df = pd.DataFrame({"date": [], "symbol": [], "close": []})
    with pytest.raises(ValueError, match="missing columns"):
        require_ohlcv_columns(df, source="test")
