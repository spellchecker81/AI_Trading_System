import os
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"
import sys
print("CHECKPOINT 1: basic imports done", flush=True)

import inspect
from functools import partial
from pathlib import Path
import asyncio
print("CHECKPOINT 2: stdlib imports done", flush=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
print("CHECKPOINT 3: asyncio loop set up", flush=True)

import streamlit as st
import pandas as pd
print("CHECKPOINT 4: streamlit + pandas imported", flush=True)

from market_data.ibkr_market_data import get_historical_data
print("CHECKPOINT 5: ibkr_market_data imported", flush=True)

from indicators.technical_indicators import calculate_indicators
print("CHECKPOINT 6: technical_indicators imported", flush=True)

from backtesting.backtester import Backtester
print("CHECKPOINT 7: Backtester imported", flush=True)

from strategies.macd_momentum import macd_momentum_signal
print("CHECKPOINT 8: macd_momentum imported", flush=True)

from strategies.rsi_mean_reversion import rsi_mean_reversion_signal
print("CHECKPOINT 9: rsi_mean_reversion imported", flush=True)


st.set_page_config(
    page_title="AI Trading System",
    layout="wide"
)
print("CHECKPOINT 10: set_page_config done", flush=True)


def build_strategy_callable(strategy_choice, buy_rsi, sell_rsi):
    """
    Wire the RSI slider values into rsi_mean_reversion_signal if that
    function accepts them, otherwise fall back to calling it with just
    the data (so this doesn't hard-crash if the strategy signature
    hasn't been updated yet).
    """
    if strategy_choice == "RSI Mean Reversion":
        sig_params = inspect.signature(rsi_mean_reversion_signal).parameters
        if "buy_threshold" in sig_params and "sell_threshold" in sig_params:
            return partial(
                rsi_mean_reversion_signal,
                buy_threshold=buy_rsi,
                sell_threshold=sell_rsi
            )
        else:
            st.warning(
                "rsi_mean_reversion_signal() doesn't accept buy_threshold/"
                "sell_threshold yet, so the RSI sliders aren't affecting "
                "this backtest. See note below the results."
            )
            return rsi_mean_reversion_signal
    else:
        return macd_momentum_signal


def run_backtest(symbol, capital, strategy_fn, take_profit_pct, stop_loss_pct, trailing_pct):

    data = get_historical_data(symbol=symbol, days=365)

    if data.empty:
        st.error("No market data returned.")
        return None, None

    data = calculate_indicators(data)

    if len(data) < 200:
        st.error(
            f"Only {len(data)} bars of data available, but indicators/backtest "
            "need at least 200 to warm up. Try a longer lookback."
        )
        return None, None

    backtester = Backtester(
        data,
        initial_capital=capital,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        trailing_pct=trailing_pct
    )

    results = backtester.run(strategy_fn)

    return results, data


st.title("AI Trading System v0.1")
st.divider()

col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Symbol", value="AAPL").strip().upper()

with col2:
    capital = st.number_input(
        "Initial Capital",
        min_value=1000,
        value=100000,
        step=1000
    )

strategy_choice = st.radio(
    "Strategy",
    options=["RSI Mean Reversion", "MACD Momentum"],
    horizontal=True
)

st.subheader("Indicator Settings")

ind_col1, ind_col2 = st.columns(2)

with ind_col1:
    buy_rsi = st.slider(
        "RSI Buy Threshold",
        min_value=10,
        max_value=50,
        value=30,
        disabled=(strategy_choice != "RSI Mean Reversion"),
        help="Only used when Strategy is set to RSI Mean Reversion."
    )

with ind_col2:
    sell_rsi = st.slider(
        "RSI Sell Threshold",
        min_value=50,
        max_value=90,
        value=70,
        disabled=(strategy_choice != "RSI Mean Reversion"),
        help="Only used when Strategy is set to RSI Mean Reversion."
    )

st.subheader("Exit Rules")
st.caption("Set any of these to 0 to disable that exit rule entirely.")

exit_col1, exit_col2, exit_col3 = st.columns(3)

with exit_col1:
    take_profit = st.slider(
        "Take Profit (%)",
        min_value=0,
        max_value=100,
        value=20,
        help="Fixed target: exits once price is this % above your entry price."
    )

with exit_col2:
    stop_loss = st.slider(
        "Stop Loss (%)",
        min_value=0,
        max_value=50,
        value=8,
        help="Fixed floor: exits once price is this % below your entry price."
    )

with exit_col3:
    trailing_profit = st.slider(
        "Trailing Stop (%)",
        min_value=0,
        max_value=50,
        value=10,
        help=(
            "Tracks the highest price reached since entry, and exits once "
            "price pulls back this % from that peak. Different from Take "
            "Profit: it lets winners run and locks in gains on the way "
            "back down, rather than exiting at a fixed target."
        )
    )

st.divider()
print("CHECKPOINT 11: all widgets laid out, reached button", flush=True)

run_clicked = st.button("Run Backtest", type="primary")

if run_clicked:
    strategy_fn = build_strategy_callable(strategy_choice, buy_rsi, sell_rsi)

    with st.spinner(f"Downloading data and backtesting {symbol}..."):
        results, data = run_backtest(
            symbol=symbol,
            capital=capital,
            strategy_fn=strategy_fn,
            take_profit_pct=take_profit if take_profit > 0 else None,
            stop_loss_pct=stop_loss if stop_loss > 0 else None,
            trailing_pct=trailing_profit if trailing_profit > 0 else None
        )

    if results is not None:
        st.session_state["results"] = results
        st.session_state["data"] = data
        st.session_state["symbol"] = symbol

# Persist results across reruns (e.g. when sliders move after a run)
# instead of losing them until the button is clicked again.
if "results" in st.session_state:
    results = st.session_state["results"]
    data = st.session_state["data"]
    symbol = st.session_state["symbol"]

    st.success("Backtest Complete")

    st.subheader("Performance")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Symbol", symbol)
    m2.metric("Final Value", f"${results['final_value']:,.2f}")
    m3.metric("Return", f"{results['return_percent']:.2f}%")
    m4.metric("Trades", len(results["trades"]))

    with st.expander("Raw trade log"):
        if results["trades"]:
            st.dataframe(pd.DataFrame(results["trades"]), use_container_width=True)
        else:
            st.write("No trades were triggered over this period.")

    st.subheader("Equity Curve")
    equity_df = pd.DataFrame(results["equity_curve"])
    if not equity_df.empty:
        st.line_chart(equity_df.set_index("date")["equity"])
    else:
        st.write("No equity data recorded.")

    with st.expander("Price chart (reference)"):
        st.line_chart(data.set_index("date")["close"])
else:
    st.info("Set your parameters above and click **Run Backtest**.")