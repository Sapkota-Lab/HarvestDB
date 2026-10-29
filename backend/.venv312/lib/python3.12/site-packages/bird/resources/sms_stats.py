"""``client.sms.stats`` — aggregate statistics over the workspace's SMS traffic.

The generated base carries the outbound reads; this wrapper exists to nest the
inbound family under them, so a caller reaches received-message counts at
``client.sms.stats.inbound`` rather than a second top-level resource.
"""

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.sms_stats_gen import AsyncSmsStatsBase, SmsStatsBase
from bird.resources.sms_stats_inbound_gen import AsyncSmsStatsInbound, SmsStatsInbound


class SmsStats(SmsStatsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.inbound = SmsStatsInbound(client)


class AsyncSmsStats(AsyncSmsStatsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.inbound = AsyncSmsStatsInbound(client)
