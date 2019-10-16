import math
from decimal import Decimal
from enum import IntEnum
from typing import Dict, Iterable, Optional, Tuple, Type

import ib_insync as IB  # type: ignore
import pandas as pd  # type: ignore
from bankroll.marketdata import StreamingMarketDataProvider
from bankroll.model import (
    Bond,
    Cash,
    Currency,
    Forex,
    Future,
    FutureOption,
    Instrument,
    Option,
    Quote,
    Stock,
)

from rx.core.typing import Observable


def _stockContract(stock: Stock) -> IB.Contract:
    return IB.Stock(
        symbol=stock.symbol,
        exchange=f"SMART:{stock.exchange}" if stock.exchange else "SMART",
        currency=stock.currency.name,
    )


def _bondContract(bond: Bond) -> IB.Contract:
    return IB.Bond(
        symbol=bond.symbol,
        exchange=bond.exchange or "SMART",
        currency=bond.currency.name,
    )


def _optionContract(option: Option, cls: Type[IB.Contract] = IB.Option) -> IB.Contract:
    lastTradeDate = option.expiration.strftime("%Y%m%d")
    defaultExchange = "" if issubclass(cls, IB.FuturesOption) else "SMART"

    return cls(
        localSymbol=option.symbol,
        exchange=option.exchange or defaultExchange,
        currency=option.currency.name,
        lastTradeDateOrContractMonth=lastTradeDate,
        right=option.optionType.value,
        strike=float(option.strike),
        multiplier=str(option.multiplier),
    )


def _futuresContract(future: Future) -> IB.Contract:
    lastTradeDate = future.expiration.strftime("%Y%m%d")

    return IB.Future(
        symbol=future.symbol,
        exchange=future.exchange or "",
        currency=future.currency.name,
        multiplier=str(future.multiplier),
        lastTradeDateOrContractMonth=lastTradeDate,
    )


def _forexContract(forex: Forex) -> IB.Contract:
    return IB.Forex(
        pair=forex.symbol,
        currency=forex.currency.name,
        exchange=forex.exchange or "IDEALPRO",
    )


def contract(instrument: Instrument) -> IB.Contract:
    if isinstance(instrument, Stock):
        return _stockContract(instrument)
    elif isinstance(instrument, Bond):
        return _bondContract(instrument)
    elif isinstance(instrument, FutureOption):
        return _optionContract(instrument, cls=IB.FuturesOption)
    elif isinstance(instrument, Option):
        return _optionContract(instrument)
    elif isinstance(instrument, Future):
        return _futuresContract(instrument)
    elif isinstance(instrument, Forex):
        return _forexContract(instrument)
    else:
        raise ValueError(f"Unexpected type of instrument: {instrument!r}")


# https://interactivebrokers.github.io/tws-api/market_data_type.html
class _MarketDataType(IntEnum):
    LIVE = 1
    FROZEN = 2
    DELAYED = 3
    DELAYED_FROZEN = 4


class IBDataProvider(StreamingMarketDataProvider):
    def __init__(
        self,
        client: IB.IB,
        dataType: Optional[_MarketDataType] = _MarketDataType.DELAYED_FROZEN,
    ):
        self._client = client

        if dataType is not None:
            self._client.reqMarketDataType(dataType.value)

        super().__init__()

    def qualifyContracts(
        self, instruments: Iterable[Instrument]
    ) -> Dict[Instrument, IB.Contract]:
        # IB.Contract is not guaranteed to be hashable, so we orient the table this way, albeit less useful.
        # TODO: Check uniqueness of instruments
        contractsByInstrument: Dict[Instrument, IB.Contract] = {
            i: contract(i) for i in instruments
        }

        self._client.qualifyContracts(*contractsByInstrument.values())

        return contractsByInstrument

    def fetchHistoricalData(self, instrument: Instrument) -> pd.DataFrame:
        contractsByInstrument = self.qualifyContracts([instrument])
        data = self._client.reqHistoricalData(
            contractsByInstrument[instrument],
            endDateTime="",
            durationStr="10 Y",
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=True,
            formatDate=1,
        )
        return IB.util.df(data)

    def _quoteFromTicker(self, ticker: IB.Ticker, instrument: Instrument) -> Quote:
        bid: Optional[Cash] = None
        ask: Optional[Cash] = None
        last: Optional[Cash] = None
        close: Optional[Cash] = None

        factor = 1

        # Tickers are quoted in GBX despite all the other data being in GBP.
        if instrument.currency == Currency.GBP:
            factor = 100

        if (ticker.bid and math.isfinite(ticker.bid)) and not ticker.bidSize == 0:
            bid = Cash(
                currency=instrument.currency, quantity=Decimal(ticker.bid) / factor
            )
        if (ticker.ask and math.isfinite(ticker.ask)) and not ticker.askSize == 0:
            ask = Cash(
                currency=instrument.currency, quantity=Decimal(ticker.ask) / factor
            )
        if (ticker.last and math.isfinite(ticker.last)) and not ticker.lastSize == 0:
            last = Cash(
                currency=instrument.currency, quantity=Decimal(ticker.last) / factor
            )
        if ticker.close and math.isfinite(ticker.close):
            close = Cash(
                currency=instrument.currency, quantity=Decimal(ticker.close) / factor
            )

        return Quote(bid=bid, ask=ask, last=last, close=close)

    def fetchQuotes(
        self,
        instruments: Iterable[Instrument],
        # TODO: Remove this (but it will break backwards compatibility).
        dataType: Optional[_MarketDataType] = None,
    ) -> Iterable[Tuple[Instrument, Quote]]:
        if dataType is not None:
            self._client.reqMarketDataType(dataType.value)

        contractsByInstrument = self.qualifyContracts(instruments)

        # Note: this blocks until all tickers come back. When we want this to be async, we'll need to use reqMktData().
        # See https://github.com/jspahrsummers/bankroll/issues/13.
        tickers = self._client.reqTickers(*contractsByInstrument.values())

        for ticker in tickers:
            instrument = next(
                (i for (i, c) in contractsByInstrument.items() if c == ticker.contract)
            )

            yield (instrument, self._quoteFromTicker(ticker, instrument))

    def subscribeToQuotes(
        self, instruments: Iterable[Instrument]
    ) -> Observable[Tuple[Instrument, Quote]]:
        pass
