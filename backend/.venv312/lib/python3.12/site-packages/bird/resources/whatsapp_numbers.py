"""``client.whatsapp.numbers`` — the WhatsApp numbers this workspace can send from.

The generated base carries the number reads; this wrapper exists to nest the
business profile under them, so a caller reaches it at
``client.whatsapp.numbers.profile`` rather than a second top-level resource.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.whatsapp_numbers_gen import AsyncWhatsappNumbersBase, WhatsappNumbersBase
from bird.resources.whatsapp_numbers_profile_gen import (
    AsyncWhatsappNumbersProfile,
    WhatsappNumbersProfile,
)


class WhatsappNumbers(WhatsappNumbersBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.profile = WhatsappNumbersProfile(client)


class AsyncWhatsappNumbers(AsyncWhatsappNumbersBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.profile = AsyncWhatsappNumbersProfile(client)
