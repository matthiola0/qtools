# qtools

Personal quant research toolkit. Data loaders for TW / US / crypto markets, a vectorized backtest engine, and factor / performance metrics.

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
- **`qtools.backtest`** — vectorized long-only / long-short engine with a
  cost model (commission + slippage + asymmetric tax on sells). No look-ahead:
  positions held at close of day t earn day t+1's return.
- **`qtools.metrics`** — standard performance stats (Sharpe, Sortino, MDD,
  Calmar) and factor evaluation (IC, IR, quantile spreads, turnover).
- **`qtools.utils.dates`** — trading calendars and rebalance-date selection.

## Data conventions

All price loaders return a long-format DataFrame with columns:

| column | dtype | notes |
|---|---|---|
| `date` | datetime64[ns] | bar close timestamp |
| `symbol` | str | native ticker (e.g. `AAPL`, `2330`, `BTC/USDT`) |
| `open` / `high` / `low` / `close` | float | adjusted close when `adjust=True` |
| `volume` | float | |

Signals and weights are wide-format: index = `date`, columns = `symbol`.

## Modules

| Module | Exports |
|---|---|
| `qtools.data.loaders.us` | `get_us_prices`, `get_sp500_constituents` |
| `qtools.data.loaders.twse` | `get_tw_prices`, `get_tw50_constituents` |
| `qtools.data.loaders.crypto` | `get_crypto_prices`, `get_top_pairs` |
| `qtools.data.cache` | `read_parquet`, `write_parquet`, `clear_cache` |
| `qtools.backtest` | `BacktestEngine`, `BacktestResult`, `CostModel`, `TW_EQUITY`, `US_EQUITY`, `CRYPTO` |
| `qtools.backtest.portfolio` | `signal_to_weights`, `equal_weight` |
| `qtools.metrics.performance` | `sharpe`, `sortino`, `max_drawdown`, `calmar`, `annualized_return`, `annualized_vol` |
| `qtools.metrics.factor` | `information_coefficient`, `information_ratio`, `quantile_returns`, `turnover`, `factor_report` |
| `qtools.metrics.plots` | `plot_cumulative_returns`, `plot_drawdown`, `plot_quantile_returns`, `plot_ic_timeseries` |
| `qtools.utils.dates` | `trading_calendar`, `resample_to_last` |

## Example

```python
from qtools.backtest import BacktestEngine, US_EQUITY
from qtools.backtest.portfolio import signal_to_weights
from qtools.data.loaders.us import get_sp500_constituents, get_us_prices
from qtools.metrics.performance import sharpe

prices = get_us_prices(get_sp500_constituents(), "2020-01-01", "2024-12-31")
close = prices.pivot(index="date", columns="symbol", values="close")

# 12-1 momentum
signal = close.shift(21) / close.shift(252 + 21) - 1

weights = signal_to_weights(signal, n_quantiles=5, long_short=True, rebalance="M")
result = BacktestEngine(prices, cost_model=US_EQUITY).run(weights)

print(f"Sharpe: {sharpe(result.returns):+.2f}")
```

## Testing

```bash
pytest -v
```
