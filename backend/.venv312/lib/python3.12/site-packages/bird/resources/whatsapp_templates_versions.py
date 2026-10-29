"""``client.whatsapp.templates.versions`` — one template's submissions.

A version is where content lives; the template above it carries only the handle.
This wrapper nests the per-language reads under the version they belong to.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.whatsapp_templates_versions_gen import (
    AsyncWhatsappTemplatesVersionsBase,
    WhatsappTemplatesVersionsBase,
)
from bird.resources.whatsapp_templates_versions_languages_gen import (
    AsyncWhatsappTemplatesVersionsLanguages,
    WhatsappTemplatesVersionsLanguages,
)


class WhatsappTemplatesVersions(WhatsappTemplatesVersionsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.languages = WhatsappTemplatesVersionsLanguages(client)


class AsyncWhatsappTemplatesVersions(AsyncWhatsappTemplatesVersionsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.languages = AsyncWhatsappTemplatesVersionsLanguages(client)
