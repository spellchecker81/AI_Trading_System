from market_data.ibkr_market_data import get_historical_data
from indicators.technical_indicators import calculate_indicators

from strategies.rsi_mean_reversion import rsi_mean_reversion_signal
from strategies.macd_momentum import macd_momentum_signal


symbol = "AAPL"


data = get_historical_data(
    symbol,
    250
)

data = calculate_indicators(data)


print("\nRSI Strategy:")
print(
    rsi_mean_reversion_signal(data)
)


print("\nMACD Strategy:")
print(
    macd_momentum_signal(data)
)