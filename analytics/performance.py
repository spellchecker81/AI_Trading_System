import pandas as pd
import numpy as np


def calculate_performance(
    equity_curve,
    trades,
    initial_capital
):

    equity = pd.Series(equity_curve)

    returns = equity.pct_change().dropna()


    total_return = (
        equity.iloc[-1] /
        initial_capital - 1
    ) * 100


    # Drawdown calculation
    running_max = equity.cummax()

    drawdown = (
        equity - running_max
    ) / running_max


    max_drawdown = (
        drawdown.min() * 100
    )


    # Sharpe ratio
    if len(returns) > 1:

        sharpe = (
            returns.mean() /
            returns.std()
        ) * np.sqrt(252)

    else:
        sharpe = 0


    # Trade statistics

    wins = []
    losses = []


    for i in range(0, len(trades)-1, 2):

        if (
            trades[i]["action"] == "BUY"
            and trades[i+1]["action"] == "SELL"
        ):

            buy_price = trades[i]["price"]
            sell_price = trades[i+1]["price"]

            result = (
                sell_price -
                buy_price
            ) / buy_price


            if result > 0:
                wins.append(result)

            else:
                losses.append(result)


    win_rate = (
        len(wins) /
        (len(wins)+len(losses))
        * 100
        if wins or losses
        else 0
    )


    return {

        "total_return_%":
            round(total_return,2),

        "max_drawdown_%":
            round(max_drawdown,2),

        "sharpe_ratio":
            round(sharpe,2),

        "number_of_trades":
            len(trades)//2,

        "win_rate_%":
            round(win_rate,2),

        "average_win_%":
            round(
                np.mean(wins)*100,2
            )
            if wins else 0,

        "average_loss_%":
            round(
                np.mean(losses)*100,2
            )
            if losses else 0
    }