import pandas as pd


class Backtester:

    def __init__(
        self,
        data,
        initial_capital=100000,
        take_profit_pct=None,   # e.g. 10 for a fixed +10% target
        stop_loss_pct=None,     # e.g. 5 for a fixed -5% stop
        trailing_pct=None       # e.g. 10 for a 10% trailing stop off the peak
    ):
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.shares = 0
        self.trades = []
        self.equity_curve = []

        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.trailing_pct = trailing_pct

        # position-tracking state, reset on each entry
        self.entry_price = None
        self.peak_price = None

    def _check_exit(self, price):
        """Return a reason string if an exit condition is hit, else None."""
        if self.shares == 0 or self.entry_price is None:
            return None

        # update the running peak since entry (needed for trailing stop)
        if self.peak_price is None or price > self.peak_price:
            self.peak_price = price

        if self.take_profit_pct is not None:
            target = self.entry_price * (1 + self.take_profit_pct / 100)
            if price >= target:
                return "TAKE_PROFIT"

        if self.stop_loss_pct is not None:
            floor = self.entry_price * (1 - self.stop_loss_pct / 100)
            if price <= floor:
                return "STOP_LOSS"

        if self.trailing_pct is not None:
            trail_floor = self.peak_price * (1 - self.trailing_pct / 100)
            if price <= trail_floor:
                return "TRAILING_STOP"

        return None

    def run(self, strategy_function):

        for i in range(len(self.data)):

            current_data = self.data.iloc[:i + 1]

            if len(current_data) < 200:
                continue

            price = current_data.iloc[-1]["close"]

            # 1. Check exit conditions FIRST if we're holding a position.
            #    This takes priority over the strategy's own SELL signal.
            exit_reason = self._check_exit(price)

            if exit_reason and self.shares > 0:
                proceeds = self.shares * price
                self.cash += proceeds

                self.trades.append({
                    "action": "SELL",
                    "reason": exit_reason,
                    "price": price,
                    "shares": self.shares
                })

                self.shares = 0
                self.entry_price = None
                self.peak_price = None

            else:
                # 2. Otherwise defer to the strategy's own signal.
                signal = strategy_function(current_data)

                if signal["signal"] == "BUY" and self.shares == 0:
                    self.shares = self.cash // price
                    cost = self.shares * price
                    self.cash -= cost

                    self.entry_price = price
                    self.peak_price = price

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
                        "reason": "STRATEGY_SIGNAL",
                        "price": price,
                        "shares": self.shares
                    })

                    self.shares = 0
                    self.entry_price = None
                    self.peak_price = None

            # 3. Record equity EVERY bar, not just on trades.
            self.equity_curve.append({
                "date": current_data.iloc[-1]["date"],
                "equity": self.cash + self.shares * price
            })

        final_price = self.data.iloc[-1]["close"]
        portfolio_value = self.cash + self.shares * final_price

        return {
            "initial_capital": self.initial_capital,
            "final_value": portfolio_value,
            "return_percent": ((portfolio_value / self.initial_capital) - 1) * 100,
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }