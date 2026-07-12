from rules.strategy_schema import (
    Rule,
    TradingStrategy
)


strategy = TradingStrategy(

    name="RSI Mean Reversion",

    symbol="AAPL",

    entry_rules=[
        Rule(
            indicator="RSI",
            operator="<",
            value=30
        )
    ],

    exit_rules=[
        Rule(
            indicator="RSI",
            operator=">",
            value=70
        )
    ],

    stop_loss=8

)


print(strategy)