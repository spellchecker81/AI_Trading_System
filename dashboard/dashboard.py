import os
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"
import sys

from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from market_data.ibkr_market_data import get_historical_data

from indicators.technical_indicators import calculate_indicators

from backtesting.backtester import Backtester

from strategies.macd_momentum import macd_momentum_signal

from strategies.rsi_mean_reversion import rsi_mean_reversion_signal

from strategies.ema21_trend import ema21_trend_signal


st.set_page_config(
    page_title="AI Trading System",
    layout="wide"
)


# ---------------------------------------------------------------------
# Appearance: larger/bolder base font, plus a Light / Dark / System
# theme switch. Streamlit's own theme is fixed at server start, so this
# works by injecting CSS that overrides colors directly - "System"
# uses a prefers-color-scheme media query so it follows the OS setting
# live rather than being pinned one way.
# ---------------------------------------------------------------------
def inject_theme_css(theme_choice):
    base_font = """
        html, body, [class*="css"] {
            font-size: 17px !important;
        }
        label, .stMarkdown p, .stCaption, div[data-testid="stMetricLabel"] {
            font-weight: 600 !important;
        }
        div[data-testid="stMetricValue"] {
            font-weight: 700 !important;
            font-size: 1.6rem !important;
        }
        h1, h2, h3 {
            font-weight: 700 !important;
        }
    """

    light_colors = """
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
        }
        [data-testid="stSidebar"] {
            background-color: #f5f5f5 !important;
        }
    """

    dark_text_selectors = """
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] div,
        [data-testid="stMarkdownContainer"] *,
        [data-testid="stMetricLabel"] *,
        [data-testid="stMetricValue"] *,
        [data-testid="stWidgetLabel"] *,
        .stRadio label, .stSlider label, .stTextInput label,
        .stNumberInput label, .stCaption, .stCaption *,
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
    """

    dark_colors = f"""
        [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #161a23 !important;
        }}
        {dark_text_selectors}
    """

    system_colors = f"""
        @media (prefers-color-scheme: light) {{
            [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
                background-color: #ffffff !important;
                color: #1a1a1a !important;
            }}
        }}
        @media (prefers-color-scheme: dark) {{
            [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
                background-color: #0e1117 !important;
                color: #ffffff !important;
            }}
            {dark_text_selectors}
        }}
    """

    if theme_choice == "Light":
        color_css = light_colors
    elif theme_choice == "Dark":
        color_css = dark_colors
    else:
        color_css = system_colors

    st.markdown(f"<style>{base_font}{color_css}</style>", unsafe_allow_html=True)


theme_choice = st.radio(
    "Appearance",
    options=["Light", "Dark", "System"],
    index=2,
    horizontal=True
)
inject_theme_css(theme_choice)


def build_strategy_callable(strategy_choice, buy_rsi, sell_rsi):
    """
    Wire the RSI slider values into whichever strategy uses RSI
    thresholds. MACD and EMA21 don't use these sliders.
    """
    if strategy_choice == "RSI Mean Reversion":
        return partial(
            rsi_mean_reversion_signal,
            buy_threshold=buy_rsi,
            sell_threshold=sell_rsi
        )
    elif strategy_choice == "EMA21 Trend":
        return ema21_trend_signal
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


def build_rsi_chart(data, trades, buy_threshold, sell_threshold):
    """
    RSI line chart that reacts live to the buy/sell threshold sliders
    (the fill zones and threshold lines always use whatever the
    sliders are currently set to, not just whatever they were when
    the backtest last ran), plus green up-arrows for BUY trades and
    red down-arrows for SELL trades plotted at each trade's date.
    """
    fig = go.Figure()

    # Oversold zone (green fill, below the buy threshold)
    fig.add_trace(go.Scatter(
        x=data["date"], y=[buy_threshold] * len(data),
        line=dict(width=0), showlegend=False, hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=data["date"], y=[0] * len(data),
        fill="tonexty", fillcolor="rgba(0, 200, 0, 0.15)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"
    ))

    # Overbought zone (red fill, above the sell threshold)
    fig.add_trace(go.Scatter(
        x=data["date"], y=[sell_threshold] * len(data),
        line=dict(width=0), showlegend=False, hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=data["date"], y=[100] * len(data),
        fill="tonexty", fillcolor="rgba(220, 0, 0, 0.15)",
        line=dict(width=0), showlegend=False, hoverinfo="skip"
    ))

    # Threshold lines
    fig.add_hline(y=buy_threshold, line_dash="dot", line_color="green",
                  annotation_text=f"Buy threshold ({buy_threshold})")
    fig.add_hline(y=sell_threshold, line_dash="dot", line_color="red",
                  annotation_text=f"Sell threshold ({sell_threshold})")

    # RSI line itself
    fig.add_trace(go.Scatter(
        x=data["date"], y=data["rsi_14"],
        mode="lines", name="RSI (14)",
        line=dict(color="#1f77b4", width=2)
    ))

    # Buy/sell trade markers, matched to the RSI value on that date
    rsi_by_date = data.set_index("date")["rsi_14"]

    buy_x, buy_y = [], []
    sell_x, sell_y = [], []

    for t in trades:
        trade_date = t["date"]
        if trade_date not in rsi_by_date.index:
            continue
        rsi_val = rsi_by_date.loc[trade_date]
        if isinstance(rsi_val, pd.Series):
            rsi_val = rsi_val.iloc[0]
        if pd.isna(rsi_val):
            continue

        if t["action"] == "BUY":
            buy_x.append(trade_date)
            buy_y.append(max(0, rsi_val - 8))
        elif t["action"] == "SELL":
            sell_x.append(trade_date)
            sell_y.append(min(100, rsi_val + 8))

    if buy_x:
        fig.add_trace(go.Scatter(
            x=buy_x, y=buy_y, mode="markers", name="Buy",
            marker=dict(symbol="triangle-up", size=13, color="green")
        ))

    if sell_x:
        fig.add_trace(go.Scatter(
            x=sell_x, y=sell_y, mode="markers", name="Sell",
            marker=dict(symbol="triangle-down", size=13, color="red")
        ))

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(range=[0, 100], title="RSI"),
        xaxis=dict(title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


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
    options=["RSI Mean Reversion", "MACD Momentum", "EMA21 Trend"],
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
        help="Only used when Strategy is set to RSI Mean Reversion. Also drives the RSI chart's threshold lines below, live."
    )

with ind_col2:
    sell_rsi = st.slider(
        "RSI Sell Threshold",
        min_value=50,
        max_value=90,
        value=70,
        disabled=(strategy_choice != "RSI Mean Reversion"),
        help="Only used when Strategy is set to RSI Mean Reversion. Also drives the RSI chart's threshold lines below, live."
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

is_running = st.session_state.get("backtest_running", False)

run_clicked = st.button(
    "Run Backtest",
    type="primary",
    disabled=is_running
)

if is_running:
    st.caption(
        "A request is already in progress - please wait for it to finish "
        "before clicking again. IBKR will time out or reject rapid repeated "
        "requests, which is the most common cause of a stuck-looking result."
    )

if run_clicked and not is_running:
    st.session_state["backtest_running"] = True
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

    st.session_state["backtest_running"] = False

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

    trades = results["trades"]
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    buy_trades = [t for t in trades if t["action"] == "BUY"]

    wins = 0
    for buy, sell in zip(buy_trades, sell_trades):
        if sell["price"] > buy["price"]:
            wins += 1
    win_rate = (wins / len(sell_trades) * 100) if sell_trades else None

    latest_atr_pct = data["atr_21_pct"].iloc[-1] if "atr_21_pct" in data.columns else None
    current_price = data["close"].iloc[-1]

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Symbol", symbol)
    m1.caption(f"${current_price:,.2f}")
    m2.metric("Final Value", f"${results['final_value']:,.2f}")
    m3.metric("Return", f"{results['return_percent']:.2f}%")
    m4.metric("Trades", len(sell_trades))
    m5.metric("Win Rate", f"{win_rate:.0f}%" if win_rate is not None else "N/A")
    m6.metric(
        "ATR (21d)",
        f"{latest_atr_pct:.2f}%" if latest_atr_pct is not None and not pd.isna(latest_atr_pct) else "N/A",
        help="21-day Average True Range as a % of price - a measure of how much this symbol typically moves day to day."
    )

    st.subheader("RSI")
    st.caption("Threshold lines and fill zones update live with the RSI Buy/Sell Threshold sliders above.")
    st.plotly_chart(
        build_rsi_chart(data, trades, buy_rsi, sell_rsi),
        use_container_width=True
    )

    with st.expander("Raw trade log", expanded=True):
        if trades:
            trade_df = pd.DataFrame(trades)
            trade_df = trade_df[["date", "action", "reason", "price", "shares"]]
            trade_df.columns = ["Date", "Action", "Reason", "Price", "Shares"]
            trade_df["Price"] = trade_df["Price"].map(lambda p: f"${p:,.2f}")
            st.dataframe(trade_df, use_container_width=True, hide_index=True)
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