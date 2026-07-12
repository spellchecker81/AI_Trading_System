def rsi_mean_reversion_signal(df, buy_threshold=30, sell_threshold=70):
    """
    RSI Mean Reversion Strategy

    Rule:
    BUY:
        RSI < buy_threshold
        AND price above 200-day moving average

    SELL:
        RSI > sell_threshold
    """

    latest = df.iloc[-1]

    if (
        latest["rsi_14"] < buy_threshold
        and latest["close"] > latest["sma_200"]
    ):
        signal = "BUY"

    elif latest["rsi_14"] > sell_threshold:
        signal = "SELL"

    else:
        signal = "HOLD"

    return {
        "strategy": "RSI Mean Reversion",
        "signal": signal,
        "rsi": latest["rsi_14"],
        "price": latest["close"]
    }