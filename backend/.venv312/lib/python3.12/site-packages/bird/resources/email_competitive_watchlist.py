from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_competitive_watchlist_gen import AsyncEmailCompetitiveWatchlistBase, EmailCompetitiveWatchlistBase
from bird.resources.email_competitive_watchlist_brands import AsyncEmailCompetitiveWatchlistBrands, EmailCompetitiveWatchlistBrands


class EmailCompetitiveWatchlist(EmailCompetitiveWatchlistBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.brands = EmailCompetitiveWatchlistBrands(client)


class AsyncEmailCompetitiveWatchlist(AsyncEmailCompetitiveWatchlistBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.brands = AsyncEmailCompetitiveWatchlistBrands(client)
