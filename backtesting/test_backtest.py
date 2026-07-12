from market_data.ibkr_market_data import get_historical_data
from indicators.technical_indicators import calculate_indicators

from strategies.macd_momentum import macd_momentum_signal

from backtesting.backtester import Backtester


data = get_historical_data(
    "AAPL",
    365
)
if data.empty:
    raise ValueError("IBKR returned no market data")
data = calculate_indicators(data)


engine = Backtester(
    data,
    initial_capital=100000
)


results = engine.run(
    macd_momentum_signal
)


print("\nBacktest Results:")
print(results)