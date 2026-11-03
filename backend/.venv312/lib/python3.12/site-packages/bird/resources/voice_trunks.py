from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.voice_trunks_gen import (
    AsyncVoiceTrunksBase,
    VoiceTrunksBase,
)
from bird.resources.voice_trunks_gateways_gen import (
    AsyncVoiceTrunksGateways,
    VoiceTrunksGateways,
)


class VoiceTrunks(VoiceTrunksBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.gateways = VoiceTrunksGateways(client)


class AsyncVoiceTrunks(AsyncVoiceTrunksBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.gateways = AsyncVoiceTrunksGateways(client)
