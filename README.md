# qtools

Personal quant research toolkit. Data loaders for TW / US / crypto markets and performance metrics.

## Install

```bash
pip install git+https://github.com/matthiola0/qtools.git
```

For development:

```bash
git clone https://github.com/matthiola0/qtools.git
cd qtools
pip install -e ".[dev]"
pytest
```

## What it does

- **`qtools.data`** — unified price loaders across three markets. Binance (ccxt)
  supports any interval from `1m` to `1w`; yfinance provides daily equity data
  for US and Taiwan. Results are cached as parquet under `~/.qtools_cache/`.
- **`qtools.metrics`** — standard performance statistics (Sharpe, Sortino, MDD,
  Calmar, annualized return / volatility).

## Data conventions

All price loaders return a long-format DataFrame with columns:

| column | dtype | notes |
|---|---|---|
| `date` | datetime64[ns] | bar close timestamp |
| `symbol` | str | native ticker (e.g. `AAPL`, `2330`, `BTC/USDT`) |
| `open` / `high` / `low` / `close` | float | adjusted close when `adjust=True` |
| `volume` | float | |

## Modules

| Module | Exports |
|---|---|
| `qtools.data.loaders.us` | `get_us_prices`, `get_sp500_constituents` |
| `qtools.data.loaders.twse` | `get_tw_prices`, `get_tw50_constituents` |
| `qtools.data.loaders.crypto` | `get_crypto_prices`, `get_top_pairs` |
| `qtools.data.cache` | `read_parquet`, `write_parquet`, `clear_cache` |
| `qtools.metrics.performance` | `sharpe`, `sortino`, `max_drawdown`, `calmar`, `annualized_return`, `annualized_vol` |

## Example

```python
from qtools.data.loaders.us import get_sp500_constituents, get_us_prices
from qtools.metrics.performance import sharpe

prices = get_us_prices(get_sp500_constituents(), "2020-01-01", "2024-12-31")
daily_ret = prices.groupby("symbol")["close"].pct_change()
print(f"Average single-name Sharpe: {sharpe(daily_ret.dropna()):+.2f}")
```

## Testing

```bash
pytest -v
```
