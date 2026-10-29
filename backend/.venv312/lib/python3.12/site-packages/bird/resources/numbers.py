"""Numbers: ``client.numbers`` — the generated held-numbers facade plus its
nested ``available`` search and ``orders`` collection, which a generated class
can't declare.

Buying is an order rather than a direct create: most complete inside the
request, but one that has to wait on a carrier comes back pending and is polled
through ``client.numbers.orders.get``.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.numbers_available_gen import AsyncNumbersAvailable, NumbersAvailable
from bird.resources.numbers_gen import AsyncNumbersBase, NumbersBase
from bird.resources.numbers_orders_gen import AsyncNumbersOrders, NumbersOrders


class Numbers(NumbersBase):
    """The numbers a workspace holds. Reach it via ``client.numbers``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.available = NumbersAvailable(client)
        self.orders = NumbersOrders(client)


class AsyncNumbers(AsyncNumbersBase):
    """The numbers a workspace holds. Reach it via ``client.numbers``."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.available = AsyncNumbersAvailable(client)
        self.orders = AsyncNumbersOrders(client)
