"""Versions: ``client.email.templates.versions`` — the generated version facade
plus its nested ``languages`` collection, which a generated class can't declare.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_templates_versions_gen import AsyncEmailTemplatesVersionsBase
from bird.resources.email_templates_versions_gen import EmailTemplatesVersionsBase
from bird.resources.email_templates_versions_languages_gen import (
    AsyncEmailTemplatesVersionsLanguages,
    EmailTemplatesVersionsLanguages,
)


class EmailTemplatesVersions(EmailTemplatesVersionsBase):
    """A template's draft and its published versions. Reach it via ``client.email.templates.versions``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.languages = EmailTemplatesVersionsLanguages(client)


class AsyncEmailTemplatesVersions(AsyncEmailTemplatesVersionsBase):
    """Async mirror of `EmailTemplatesVersions`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.languages = AsyncEmailTemplatesVersionsLanguages(client)
