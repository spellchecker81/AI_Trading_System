def rsi_mean_reversion_signal(df):
    """
    RSI Mean Reversion Strategy

    Rule:
    BUY:
        RSI < 30
        AND price above 200-day moving average

    SELL:
        RSI > 70
    """

    latest = df.iloc[-1]

    signals = []

    if (
        latest["rsi_14"] < 30
        and latest["close"] > latest["sma_200"]
    ):
        signals.append("BUY")

    elif latest["rsi_14"] > 70:
        signals.append("SELL")

    else:
        signals.append("HOLD")

    return {
        "strategy": "RSI Mean Reversion",
        "signal": signals[0],
        "rsi": latest["rsi_14"],
        "price": latest["close"]
    }