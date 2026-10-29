"""SMS template identities, versions, and language content."""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.sms_templates_gen import AsyncSmsTemplatesBase, SmsTemplatesBase
from bird.resources.sms_templates_versions import (
    AsyncSmsTemplatesVersions,
    SmsTemplatesVersions,
)


class SmsTemplates(SmsTemplatesBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.versions = SmsTemplatesVersions(client)


class AsyncSmsTemplates(AsyncSmsTemplatesBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.versions = AsyncSmsTemplatesVersions(client)
