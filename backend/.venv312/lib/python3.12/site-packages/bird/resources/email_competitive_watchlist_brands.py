from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_competitive_watchlist_brands_gen import AsyncEmailCompetitiveWatchlistBrandsBase, EmailCompetitiveWatchlistBrandsBase
from bird.resources.email_competitive_watchlist_brands_campaigns_gen import AsyncEmailCompetitiveWatchlistBrandsCampaigns, EmailCompetitiveWatchlistBrandsCampaigns


class EmailCompetitiveWatchlistBrands(EmailCompetitiveWatchlistBrandsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.campaigns = EmailCompetitiveWatchlistBrandsCampaigns(client)


class AsyncEmailCompetitiveWatchlistBrands(AsyncEmailCompetitiveWatchlistBrandsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.campaigns = AsyncEmailCompetitiveWatchlistBrandsCampaigns(client)
