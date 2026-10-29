from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.amb_stats_gen import AsyncAmbStatsBase, AmbStatsBase
from bird.resources.amb_stats_conversations_gen import AsyncAmbStatsConversations, AmbStatsConversations
from bird.resources.amb_stats_inbound_gen import AsyncAmbStatsInbound, AmbStatsInbound


class AmbStats(AmbStatsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.conversations = AmbStatsConversations(client)
        self.inbound = AmbStatsInbound(client)


class AsyncAmbStats(AsyncAmbStatsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.conversations = AsyncAmbStatsConversations(client)
        self.inbound = AsyncAmbStatsInbound(client)
