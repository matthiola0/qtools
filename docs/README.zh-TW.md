# qtools

> **Languages**: [English](../README.md) · **繁體中文**

個人量化研究工具包。涵蓋台股 / 美股 / 加密三市場的資料 loader、向量化回測引擎、因子與績效指標。

## 安裝

```bash
pip install git+https://github.com/matthiola0/qtools.git
```

開發模式：

```bash
git clone https://github.com/matthiola0/qtools.git
cd qtools
pip install -e ".[dev]"
pytest
```

## 功能模組

- **`qtools.data`** — 三市場統一價格 loader。Binance（ccxt）支援 `1m` 至 `1w` 任何頻率；yfinance 提供美股與台股日頻資料。所有結果以 parquet 快取至 `~/.qtools_cache/`。
- **`qtools.backtest`** — 向量化 long-only / long-short 回測引擎，內建成本模型（手續費 + 滑點 + 賣出證交稅不對稱）。無 look-ahead：t 日收盤持倉賺取 t+1 日報酬。
- **`qtools.metrics`** — 標準績效統計（Sharpe / Sortino / MDD / Calmar）與因子評估（IC / IR / quantile spread / turnover）。
- **`qtools.utils.dates`** — 交易日曆與 rebalance 日期生成。

## 資料規範

所有價格 loader 回傳 long-format DataFrame：

| 欄位 | dtype | 備註 |
|---|---|---|
| `date` | datetime64[ns] | 收盤時間戳 |
| `symbol` | str | 原生 ticker（如 `AAPL`、`2330`、`BTC/USDT`） |
| `open` / `high` / `low` / `close` | float | `adjust=True` 時為調整後收盤 |
| `volume` | float | |

訊號與權重採 wide-format：index = `date`，columns = `symbol`。

## 模組對照

| 模組 | 匯出函式 |
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

## CLI

安裝 qtools 後會註冊 `qtools` 指令：

```bash
# 日 K（預設）
qtools fetch us AAPL TSLA --start 2024-01-01 --end 2024-12-31

# 日內：Yahoo 限 1 分鐘 K 線只能抓最近 7 天
qtools fetch tw 2330 --start 2024-01-01 --end 2024-06-30 --interval 1h

# 加密日內：Binance 沒有歷史限制
qtools fetch crypto BTC/USDT ETH/USDT --start 2024-04-01 --end 2024-04-02 --interval 1m

# 直接寫到 parquet
qtools fetch us AAPL --start 2024-01-01 --end 2024-06-30 -o aapl.parquet

# 列出預設股票池
qtools universe us      # S&P 500（從 Wikipedia 抓）
qtools universe tw      # 台灣 50 成分股（snapshot）
qtools universe crypto  # 24h 成交量 top 30 USDT pairs
```

支援頻率：美股 / 台股 `1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo`；Binance 額外支援 `3m, 2h, 4h, 6h, 8h, 12h, 3d, 1w, 1M`。Yahoo 對日內歷史有限制（例如 1m → 最近 7 天、1h → 最近 730 天）。

每次 fetch 會快取到 `~/.qtools_cache/<market>_prices/<hash>.parquet`；相同參數第二次呼叫從磁碟讀取（毫秒級）。

## Python API

```python
from qtools.backtest import BacktestEngine, US_EQUITY
from qtools.backtest.portfolio import signal_to_weights
from qtools.data.loaders.us import get_sp500_constituents, get_us_prices
from qtools.metrics.performance import sharpe

prices = get_us_prices(get_sp500_constituents(), "2020-01-01", "2024-12-31")
close = prices.pivot(index="date", columns="symbol", values="close")

# 12-1 動量
signal = close.shift(21) / close.shift(252 + 21) - 1

weights = signal_to_weights(signal, n_quantiles=5, long_short=True, rebalance="M")
result = BacktestEngine(prices, cost_model=US_EQUITY).run(weights)

print(f"Sharpe: {sharpe(result.returns):+.2f}")
```

## 測試

```bash
pytest -v
```

42 個 unit test，涵蓋：資料快取、日期工具、組合建構、回測引擎、因子指標、績效統計、CLI。
