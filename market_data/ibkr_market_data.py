import asyncio

# ib_insync's dependency "eventkit" calls asyncio.get_event_loop() at
# IMPORT time, which raises RuntimeError if the importing thread has
# no event loop set yet. Streamlit executes scripts on a background
# "ScriptRunner" thread (not the main thread), which has no loop by
# default - so this has to run before importing ib_insync, on
# whichever thread happens to import this module first.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from ib_insync import IB, Stock
import pandas as pd
import atexit
import logging
import os
import threading

logging.basicConfig(level=logging.WARNING)

# --- Dedicated background event loop -----------------------------------
# Streamlit reruns the whole script on every interaction (including
# slider drags), and can execute different reruns on different worker
# threads from its internal thread pool. The top of dashboard.py used
# to call asyncio.set_event_loop(asyncio.new_event_loop()) on each
# rerun - if that landed on a new thread, it created a NEW event loop
# with no relationship to the one our persistent IBKR connection's
# socket was actually registered on, so requests would silently hang
# until they hit our manual timeout, regardless of how long you waited
# between attempts.
#
# The fix: run the IB connection and every request on ONE dedicated
# background thread with its own event loop that's created exactly
# once at import time and never touched again, no matter which thread
# Streamlit uses to execute a given rerun. All calls in from the main
# thread go through asyncio.run_coroutine_threadsafe().
_loop = asyncio.new_event_loop()


def _run_loop_forever():
    asyncio.set_event_loop(_loop)
    _loop.run_forever()


_loop_thread = threading.Thread(target=_run_loop_forever, daemon=True)
_loop_thread.start()

_ib = None
_connection_lock = threading.Lock()

# Derived from the process ID instead of hardcoded, so this can never
# collide with a leftover/zombie process using a different PID.
CLIENT_ID = (os.getpid() % 9000) + 100


def _call(coro, timeout):
    """Submit a coroutine to the dedicated background loop from
    whatever thread Streamlit is currently running on, and block until
    it completes or times out."""
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=timeout)


async def _connect_async(host, port, client_id, timeout):
    global _ib

    if _ib is not None and _ib.isConnected():
        return _ib

    if _ib is not None:
        try:
            _ib.disconnect()
        except Exception:
            pass

    _ib = IB()
    print(f"[ibkr] Connecting with clientId={client_id}...", flush=True)
    await _ib.connectAsync(host=host, port=port, clientId=client_id, timeout=timeout)
    return _ib


def _get_connection(host="127.0.0.1", port=7497, client_id=CLIENT_ID, timeout=10):
    with _connection_lock:
        return _call(_connect_async(host, port, client_id, timeout), timeout=timeout + 5)


@atexit.register
def _cleanup_connection():
    global _ib
    if _ib is not None and _ib.isConnected():
        try:
            _ib.disconnect()
        except Exception:
            pass


def get_historical_data(symbol, days=30):

    try:
        ib = _get_connection()
        print(f"[get_historical_data] Requesting symbol='{symbol}', days={days}", flush=True)

        contract = Stock(symbol, "SMART", "USD")

        try:
            _call(ib.qualifyContractsAsync(contract), timeout=15)
        except (asyncio.TimeoutError, TimeoutError):
            print(
                f"[get_historical_data] TIMED OUT qualifying contract for "
                f"'{symbol}' after 15s.",
                flush=True
            )
            return pd.DataFrame()

        duration_str = (
            f"{days // 365} Y"
            if days > 365
            else f"{days} D"
        )

        try:
            bars = _call(
                ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime="",
                    durationStr=duration_str,
                    barSizeSetting="1 day",
                    whatToShow="TRADES",
                    useRTH=True,
                    formatDate=1
                ),
                timeout=25
            )
        except (asyncio.TimeoutError, TimeoutError):
            print(
                f"[get_historical_data] TIMED OUT waiting for '{symbol}' after 25s.",
                flush=True
            )
            return pd.DataFrame()

        df = pd.DataFrame(
            [
                {
                    "date": bar.date,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume
                }
                for bar in bars
            ]
        )

        print(f"[get_historical_data] '{symbol}' returned {len(df)} rows", flush=True)
        return df

    except Exception as e:
        import traceback
        print(f"IBKR error: {e}")
        traceback.print_exc()
        return pd.DataFrame()


if __name__ == "__main__":

    data = get_historical_data("AAPL", 365)
    print(f"\nDownloaded {len(data)} rows")