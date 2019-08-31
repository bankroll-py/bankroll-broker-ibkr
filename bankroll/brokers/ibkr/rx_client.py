import ib_insync as IB  # type: ignore
from rx.core.typing import Disposable, Observable, Observer, Scheduler
from typing import Any, Optional

import rx
import rx.disposable as disposable


def reqMktData(
    client: IB.IB, contract: IB.Contract, *args: Any, **kwargs: Any
) -> Observable[IB.Ticker]:
    def _create(
        observer: Observer[IB.Ticker], scheduler: Optional[Scheduler]
    ) -> Disposable:
        d = disposable.CompositeDisposable()

        ticker = client.ticker(contract)
        if ticker:
            ticker = client.reqMktData(contract, *args, **kwargs)
            d.add(disposable.Disposable(lambda: client.cancelMktData(contract)))

        return disposable.Disposable()

    return rx.create(_create)

