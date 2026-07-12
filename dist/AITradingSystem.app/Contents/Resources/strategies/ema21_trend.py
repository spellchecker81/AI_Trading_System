def ema21_trend_signal(df):
    """
    EMA21 Trend Following Strategy

    Rule:
    BUY:
        price above EMA21
        AND price above SMA50 (confirms the trend, not just a short blip)

    SELL:
        price below EMA21

    This is a pure trend-following rule, opposite in spirit to RSI mean
    reversion - it buys strength and sells weakness, rather than buying
    dips and selling rallies. Expect it to perform differently depending
    on whether the symbol is trending or chopping sideways.
    """

    latest = df.iloc[-1]

    if (
        latest["close"] > latest["ema_21"]
        and latest["close"] > latest["sma_50"]
    ):
        signal = "BUY"

    elif latest["close"] < latest["ema_21"]:
        signal = "SELL"

    else:
        signal = "HOLD"

    return {
        "strategy": "EMA21 Trend",
        "signal": signal,
        "ema_21": latest["ema_21"],
        "price": latest["close"]
    }