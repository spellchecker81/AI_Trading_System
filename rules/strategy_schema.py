from dataclasses import dataclass, field
from typing import List


@dataclass
class Rule:

    indicator: str
    operator: str
    value: float


@dataclass
class TradingStrategy:

    name: str

    symbol: str

    entry_rules: List[Rule] = field(
        default_factory=list
    )

    exit_rules: List[Rule] = field(
        default_factory=list
    )

    stop_loss: float = None

    take_profit: float = None