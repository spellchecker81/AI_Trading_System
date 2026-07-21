import pandas as pd
import ta


def calculate_indicators(df):
    """
    Add technical indicators to price dataframe.

    Required columns:
    open
    high
    low
    close
    volume
    """

    df = df.copy()

    # RSI
    df["rsi_14"] = ta.momentum.RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    # MACD
    macd = ta.trend.MACD(
        close=df["close"],
        window_slow=26,
        window_fast=12,
        window_sign=9
    )

    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    # Moving averages
    df["sma_20"] = ta.trend.SMAIndicator(
        close=df["close"],
        window=20
    ).sma_indicator()

    df["sma_50"] = ta.trend.SMAIndicator(
        close=df["close"],
        window=50
    ).sma_indicator()

    df["sma_200"] = ta.trend.SMAIndicator(
        close=df["close"],
        window=200
    ).sma_indicator()

    # EMA 21 - used as a faster trend filter for the combined strategy
    df["ema_21"] = ta.trend.EMAIndicator(
        close=df["close"],
        window=21
    ).ema_indicator()

    # ATR (21-day) - volatility measure, also expressed as a % of price
    # so it's comparable across symbols at different price levels
    df["atr_21"] = ta.volatility.AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=21
    ).average_true_range()

    df["atr_21_pct"] = (df["atr_21"] / df["close"]) * 100

    return df


def generate_signal(df):

    latest = df.iloc[-1]

    signals = []

    # RSI rule
    if latest["rsi_14"] < 30:
        signals.append("RSI Oversold - BUY")

    elif latest["rsi_14"] > 70:
        signals.append("RSI Overbought - SELL")


    # MACD rule
    if latest["macd"] > latest["macd_signal"]:
        signals.append("MACD Bullish")

    elif latest["macd"] < latest["macd_signal"]:
        signals.append("MACD Bearish")


    return signals


if __name__ == "__main__":

    from market_data.ibkr_market_data import get_historical_data

    data = get_historical_data(
        "AAPL",
        250
    )

    result = calculate_indicators(data)

    print(result.tail())

    print("\nSignals:")
    print(generate_signal(result))