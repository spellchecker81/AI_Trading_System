import pandas as pd


class Backtester:

    def __init__(
        self,
        data,
        initial_capital=100000
    ):
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.shares = 0
        self.trades = []


    def run(self, strategy_function):

        for i in range(len(self.data)):

            current_data = self.data.iloc[:i+1]

            if len(current_data) < 200:
                continue

            signal = strategy_function(
                current_data
            )

            price = current_data.iloc[-1]["close"]


            if signal["signal"] == "BUY" and self.shares == 0:

                self.shares = self.cash // price
                cost = self.shares * price

                self.cash -= cost

                self.trades.append({
                    "action": "BUY",
                    "price": price,
                    "shares": self.shares
                })


            elif signal["signal"] == "SELL" and self.shares > 0:

                proceeds = self.shares * price

                self.cash += proceeds

                self.trades.append({
                    "action": "SELL",
                    "price": price,
                    "shares": self.shares
                })

                self.shares = 0


        final_price = self.data.iloc[-1]["close"]

        portfolio_value = (
            self.cash +
            self.shares * final_price
        )


        return {
            "initial_capital": self.initial_capital,
            "final_value": portfolio_value,
            "return_percent":
                ((portfolio_value /
                  self.initial_capital)-1)*100,
            "trades": self.trades
        }