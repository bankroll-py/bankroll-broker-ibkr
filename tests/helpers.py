import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, TypeVar

from hypothesis import settings
from hypothesis.strategies import (
    SearchStrategy,
    builds,
    dates,
    datetimes,
    decimals,
    from_regex,
    from_type,
    integers,
    just,
    lists,
    none,
    one_of,
    register_type_strategy,
    sampled_from,
    sets,
    text,
)

from bankroll.model import (
    AccountBalance,
    Activity,
    Bond,
    Cash,
    CashPayment,
    Currency,
    Forex,
    Future,
    FutureOption,
    Instrument,
    Option,
    OptionType,
    Position,
    Quote,
    Stock,
    Trade,
    TradeFlags,
)

settings.register_profile("ci", max_examples=1000, deadline=100)
settings.register_profile("dev", max_examples=10, deadline=100)
settings.load_profile(os.getenv(u"HYPOTHESIS_PROFILE", default="dev"))

T = TypeVar("T")


def cashAmounts(
    min_value: Decimal = Decimal("-1000000000"),
    max_value: Decimal = Decimal("1000000000"),
) -> SearchStrategy[Decimal]:
    return decimals(
        allow_nan=False, allow_infinity=False, min_value=min_value, max_value=max_value
    ).map(Cash.quantize)


def positionQuantities(
    min_value: Decimal = Decimal("-1000000000"),
    max_value: Decimal = Decimal("1000000000"),
    allow_zero: bool = False,
) -> SearchStrategy[Decimal]:
    s = decimals(
        allow_nan=False, allow_infinity=False, min_value=min_value, max_value=max_value
    ).map(Position.quantizeQuantity)

    if not allow_zero:
        s = s.filter(lambda x: x != 0)

    return s


def multipliers(
    min_value: Decimal = Decimal("1"), max_value: Decimal = Decimal("10000")
) -> SearchStrategy[Decimal]:
    return decimals(
        allow_nan=False, allow_infinity=False, min_value=min_value, max_value=max_value
    ).map(Instrument.quantizeMultiplier)


def strikes(
    min_value: Decimal = Decimal("1"), max_value: Decimal = Decimal("100000")
) -> SearchStrategy[Decimal]:
    return decimals(
        allow_nan=False, allow_infinity=False, min_value=min_value, max_value=max_value
    ).map(Option.quantizeStrike)


def exchanges() -> SearchStrategy[str]:
    return text(min_size=1)


def cashUSD(amount: Decimal) -> Cash:
    return Cash(currency=Currency.USD, quantity=amount)
