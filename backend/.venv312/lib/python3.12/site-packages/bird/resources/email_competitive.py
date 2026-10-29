from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_competitive_gen import AsyncEmailCompetitiveBase, EmailCompetitiveBase
from bird.resources.email_competitive_brands_gen import AsyncEmailCompetitiveBrands, EmailCompetitiveBrands
from bird.resources.email_competitive_watchlist import AsyncEmailCompetitiveWatchlist, EmailCompetitiveWatchlist


class EmailCompetitive(EmailCompetitiveBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.brands = EmailCompetitiveBrands(client)
        self.watchlist = EmailCompetitiveWatchlist(client)


class AsyncEmailCompetitive(AsyncEmailCompetitiveBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.brands = AsyncEmailCompetitiveBrands(client)
        self.watchlist = AsyncEmailCompetitiveWatchlist(client)
