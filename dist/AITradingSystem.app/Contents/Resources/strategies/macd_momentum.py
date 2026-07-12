def macd_momentum_signal(df):
    """
    MACD Momentum Strategy

    BUY:
        MACD > Signal line
        AND price above SMA50

    SELL:
        MACD < Signal line
    """

    latest = df.iloc[-1]

    if (
        latest["macd"] > latest["macd_signal"]
        and latest["close"] > latest["sma_50"]
    ):
        signal = "BUY"

    elif latest["macd"] < latest["macd_signal"]:
        signal = "SELL"

    else:
        signal = "HOLD"

    return {
        "strategy": "MACD Momentum",
        "signal": signal,
        "macd": latest["macd"],
        "macd_signal": latest["macd_signal"],
        "price": latest["close"]
    }