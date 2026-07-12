from ib_insync import IB, Stock
import pandas as pd


def get_historical_data(symbol, days=30):

    ib = IB()

    try:
        ib.connect(
            host="127.0.0.1",
            port=7497,
            clientId=2
        )

        print(f"Connected. Downloading {symbol} data...")

        contract = Stock(
            symbol,
            "SMART",
            "USD"
        )

        ib.qualifyContracts(contract)

        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr = (
                f"{days // 365} Y"
                if days > 365
                else f"{days} D"
            ),
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,
            formatDate=1
        )

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

        print(df.head())

        ib.disconnect()

        return df


    except Exception as e:
        print("Error:")
        print(e)

        if ib.isConnected():
            ib.disconnect()

        return pd.DataFrame()


if __name__ == "__main__":

    data = get_historical_data(
        "AAPL",
        365
    )

    print(
        f"\nDownloaded {len(data)} rows"
    )