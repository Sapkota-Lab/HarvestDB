"""Versions and language content under an SMS template."""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.sms_templates_versions_gen import (
    AsyncSmsTemplatesVersionsBase,
    SmsTemplatesVersionsBase,
)
from bird.resources.sms_templates_versions_languages_gen import (
    AsyncSmsTemplatesVersionsLanguages,
    SmsTemplatesVersionsLanguages,
)


class SmsTemplatesVersions(SmsTemplatesVersionsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.languages = SmsTemplatesVersionsLanguages(client)


class AsyncSmsTemplatesVersions(AsyncSmsTemplatesVersionsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.languages = AsyncSmsTemplatesVersionsLanguages(client)
