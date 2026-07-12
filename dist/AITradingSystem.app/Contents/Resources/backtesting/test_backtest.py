from market_data.ibkr_market_data import get_historical_data
from indicators.technical_indicators import calculate_indicators

from strategies.macd_momentum import macd_momentum_signal

from backtesting.backtester import Backtester

from analytics.performance import calculate_performance


# -----------------------------
# Configuration
# -----------------------------

SYMBOL = "AAPL"
LOOKBACK_DAYS = 365
INITIAL_CAPITAL = 100000


# -----------------------------
# Download market data
# -----------------------------

print(f"\nDownloading data for {SYMBOL}...")

data = get_historical_data(
    SYMBOL,
    LOOKBACK_DAYS
)


if data.empty:
    raise ValueError(
        "IBKR returned no market data"
    )


# -----------------------------
# Calculate indicators
# -----------------------------

print("\nCalculating indicators...")

data = calculate_indicators(data)


# -----------------------------
# Run backtest
# -----------------------------

print("\nRunning backtest...")

engine = Backtester(
    data,
    initial_capital=INITIAL_CAPITAL
)


results = engine.run(
    macd_momentum_signal
)


# -----------------------------
# Basic results
# -----------------------------

print("\n==============================")
print("BACKTEST RESULTS")
print("==============================")

print(
    f"Initial Capital: "
    f"${results['initial_capital']:,.2f}"
)

print(
    f"Final Value: "
    f"${float(results['final_value']):,.2f}"
)

print(
    f"Return: "
    f"{float(results['return_percent']):.2f}%"
)


# -----------------------------
# Performance metrics
# -----------------------------

performance = calculate_performance(
    results["equity_curve"],
    results["trades"],
    results["initial_capital"]
)


print("\n==============================")
print("PERFORMANCE REPORT")
print("==============================")

for key, value in performance.items():
    print(
        f"{key}: {value}"
    )


# -----------------------------
# Trade history
# -----------------------------

print("\n==============================")
print("TRADE HISTORY")
print("==============================")


for trade in results["trades"]:
    print(trade)