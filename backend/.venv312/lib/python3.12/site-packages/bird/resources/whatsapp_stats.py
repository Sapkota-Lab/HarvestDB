"""``client.whatsapp.stats`` — aggregate statistics over the workspace's WhatsApp traffic.

The generated base carries the outbound reads; this wrapper exists to nest the
inbound family under them, so a caller reaches received-message counts at
``client.whatsapp.stats.inbound`` rather than a second top-level resource.
"""

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.whatsapp_stats_gen import AsyncWhatsappStatsBase, WhatsappStatsBase
from bird.resources.whatsapp_stats_inbound_gen import (
    AsyncWhatsappStatsInbound,
    WhatsappStatsInbound,
)


class WhatsappStats(WhatsappStatsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.inbound = WhatsappStatsInbound(client)


class AsyncWhatsappStats(AsyncWhatsappStatsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.inbound = AsyncWhatsappStatsInbound(client)
