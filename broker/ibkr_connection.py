from ib_insync import IB


def connect_ibkr():
    ib = IB()

    try:
        print("Connecting to IBKR...")

        ib.connect(
            host="127.0.0.1",
            port=7497,       # Paper Trading TWS API port
            clientId=1
        )

        print("✓ Connected to IBKR")

        print("\nAccount Information:")

        account_summary = ib.accountSummary()

        for item in account_summary:
            if item.tag in [
                "NetLiquidation",
                "TotalCashValue",
                "BuyingPower"
            ]:
                print(f"{item.tag}: {item.value}")

        print("\nOpen Positions:")

        positions = ib.positions()

        if positions:
            for position in positions:
                print(
                    position.contract.symbol,
                    position.position,
                    position.avgCost
                )
        else:
            print("No open positions")

        ib.disconnect()

        print("\n✓ Disconnected from IBKR")

    except Exception as e:
        print("\n❌ Connection failed:")
        print(e)


if __name__ == "__main__":
    connect_ibkr()