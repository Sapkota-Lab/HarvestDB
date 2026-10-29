"""Templates: ``client.email.templates`` — the generated template facade plus its
nested ``versions`` and ``broadcasts`` collections, which a generated class can't
declare, and a hand-written ``create``: its body nests the draft's initial
content under a language-tag map the facade generator drops.
"""

from __future__ import annotations

from typing import Any, Mapping, TypedDict

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import EmailTemplate, EmailTemplateCreate
from bird._models import to_wire
from bird._types import RequestOptions
from bird.resources.email_templates_broadcasts_gen import (
    AsyncEmailTemplatesBroadcasts,
    EmailTemplatesBroadcasts,
)
from bird.resources.email_templates_gen import AsyncEmailTemplatesBase
from bird.resources.email_templates_gen import EmailTemplatesBase
from bird.resources.email_templates_versions import (
    AsyncEmailTemplatesVersions,
    EmailTemplatesVersions,
)

_PATH = "/v1/email/templates"


class EmailTemplateLanguageContent(TypedDict, total=False):
    """One language's content for a template's first draft. Every key is optional."""

    subject: str
    preview_text: str
    html: str
    text: str


def _create_body(
    slug: str,
    category: str,
    source: str,
    name: str | None,
    description: str | None,
    languages: Mapping[str, EmailTemplateLanguageContent] | None,
    default_language: str | None,
    on_missing_language: str | None,
    language_source_required: bool | None,
) -> dict[str, Any]:
    return to_wire(
        EmailTemplateCreate,
        {
            "slug": slug,
            "category": category,
            "source": source,
            "name": name,
            "description": description,
            "languages": languages,
            "default_language": default_language,
            "on_missing_language": on_missing_language,
            "language_source_required": language_source_required,
        },
    )


class EmailTemplates(EmailTemplatesBase):
    """Reusable email templates. Reach it via ``client.email.templates``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.versions = EmailTemplatesVersions(client)
        self.broadcasts = EmailTemplatesBroadcasts(client)

    def create(
        self,
        *,
        slug: str,
        category: str,
        source: str,
        name: str | None = None,
        description: str | None = None,
        languages: Mapping[str, EmailTemplateLanguageContent] | None = None,
        default_language: str | None = None,
        on_missing_language: str | None = None,
        language_source_required: bool | None = None,
        options: RequestOptions | None = None,
    ) -> EmailTemplate:
        """Create a template and its first editable draft, optionally with
        per-language content under ``languages``. The display name defaults to
        ``slug``, and a slug already used in the workspace is refused with a
        ``409``. Submit the draft before sending it. ``default_language``
        falls back to ``en`` unless you supply exactly one language, in which
        case that one is used, so two or more languages without ``en`` among
        them have to name it yourself.

        ```python
        template = client.email.templates.create(
            slug="welcome-email",
            category="marketing",
            source="html",
            languages={"en": {"subject": "Welcome, {{ first_name }}", "html": "<p>Hi</p>"}},
        )
        print(template.id, template.draft_version_id)
        ```
        """
        body = _create_body(
            slug,
            category,
            source,
            name,
            description,
            languages,
            default_language,
            on_missing_language,
            language_source_required,
        )
        return self._write("POST", _PATH, body, EmailTemplate, options)


class AsyncEmailTemplates(AsyncEmailTemplatesBase):
    """Async mirror of `EmailTemplates`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.versions = AsyncEmailTemplatesVersions(client)
        self.broadcasts = AsyncEmailTemplatesBroadcasts(client)

    async def create(
        self,
        *,
        slug: str,
        category: str,
        source: str,
        name: str | None = None,
        description: str | None = None,
        languages: Mapping[str, EmailTemplateLanguageContent] | None = None,
        default_language: str | None = None,
        on_missing_language: str | None = None,
        language_source_required: bool | None = None,
        options: RequestOptions | None = None,
    ) -> EmailTemplate:
        """Async mirror of `EmailTemplates.create`."""
        body = _create_body(
            slug,
            category,
            source,
            name,
            description,
            languages,
            default_language,
            on_missing_language,
            language_source_required,
        )
        return await self._write("POST", _PATH, body, EmailTemplate, options)
