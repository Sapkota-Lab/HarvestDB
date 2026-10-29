from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.amb_business_accounts_gen import AsyncAmbBusinessAccountsBase, AmbBusinessAccountsBase
from bird.resources.amb_business_accounts_events_gen import AsyncAmbBusinessAccountsEvents, AmbBusinessAccountsEvents
from bird.resources.amb_business_accounts_settings_gen import AsyncAmbBusinessAccountsSettings, AmbBusinessAccountsSettings
from bird.resources.amb_business_accounts_submissions_gen import AsyncAmbBusinessAccountsSubmissions, AmbBusinessAccountsSubmissions


class AmbBusinessAccounts(AmbBusinessAccountsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.events = AmbBusinessAccountsEvents(client)
        self.settings = AmbBusinessAccountsSettings(client)
        self.submissions = AmbBusinessAccountsSubmissions(client)


class AsyncAmbBusinessAccounts(AsyncAmbBusinessAccountsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.events = AsyncAmbBusinessAccountsEvents(client)
        self.settings = AsyncAmbBusinessAccountsSettings(client)
        self.submissions = AsyncAmbBusinessAccountsSubmissions(client)
