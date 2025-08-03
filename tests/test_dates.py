import pandas as pd

from qtools.utils.dates import resample_to_last, trading_calendar


def test_trading_calendar_us_business_days():
    cal = trading_calendar("2024-01-01", "2024-01-15", "US")
    # Only weekdays; no Jan 6-7 (weekend)
    assert cal.weekday.max() < 5


def test_trading_calendar_crypto_includes_weekends():
    cal = trading_calendar("2024-01-01", "2024-01-10", "crypto")
    assert len(cal) == 10


def test_resample_monthly_returns_last_trading_day():
    idx = pd.bdate_range("2024-01-01", "2024-03-31")
    rb = resample_to_last(idx, "M")
    assert len(rb) == 3
    assert rb[0] == pd.Timestamp("2024-01-31")
    assert rb[1] == pd.Timestamp("2024-02-29")  # leap year
    # Each rb date must be in the original trading calendar
    for d in rb:
        assert d in idx


def test_resample_weekly():
    idx = pd.bdate_range("2024-01-01", "2024-01-31")
    rb = resample_to_last(idx, "W")
    # ~4-5 Fridays in January
    assert 4 <= len(rb) <= 5


def test_resample_daily_is_passthrough():
    idx = pd.bdate_range("2024-01-01", "2024-01-15")
    rb = resample_to_last(idx, "D")
    assert list(rb) == list(idx)
