"""``client.whatsapp.templates`` — the workspace's WhatsApp template registry.

The generated base carries the registry reads; this wrapper exists to nest the
version family under them, so a caller reaches a template's content at
``client.whatsapp.templates.versions`` rather than a second top-level resource.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.whatsapp_templates_gen import AsyncWhatsappTemplatesBase, WhatsappTemplatesBase
from bird.resources.whatsapp_templates_versions import (
    AsyncWhatsappTemplatesVersions,
    WhatsappTemplatesVersions,
)


class WhatsappTemplates(WhatsappTemplatesBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.versions = WhatsappTemplatesVersions(client)


class AsyncWhatsappTemplates(AsyncWhatsappTemplatesBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.versions = AsyncWhatsappTemplatesVersions(client)
