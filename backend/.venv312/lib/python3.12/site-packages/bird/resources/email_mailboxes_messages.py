"""Mailbox messages: ``client.email.mailboxes.messages`` — the override residue
over the generated mailbox facade: ``create`` (address-list body).
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    EmailMailboxComposeRequest,
    EmailThreadMessage,
)
from bird._models import to_wire_exclude_unset
from bird._types import EmailDefaults, RequestOptions
from bird._resource import AsyncResource, Resource

_PATH = "/v1/email/mailboxes"

# The email defaults a compose body accepts, derived rather than listed so a field
# added to EmailDefaults reaches compose for free. A compose has no ``from`` (the
# mailbox is the sender) and no sending-infrastructure fields, and naming one it
# forbids would fail the request.
_COMPOSE_DEFAULT_KEYS = tuple(
    k for k in EmailDefaults.__annotations__ if k in EmailMailboxComposeRequest.model_fields
)


def _compose_body(defaults: EmailDefaults | None, **kwargs: Any) -> dict[str, Any]:
    # A per-call value always wins; an unset field falls back to the client default.
    if defaults:
        for key in _COMPOSE_DEFAULT_KEYS:
            if kwargs.get(key) is None and (value := defaults.get(key)) is not None:
                kwargs[key] = value
    return to_wire_exclude_unset(EmailMailboxComposeRequest, kwargs)


class EmailMailboxesMessages(Resource):
    """Send messages from a mailbox. Reach it via ``client.email.mailboxes.messages``."""

    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self._defaults = defaults

    def create(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Compose and send an outbound message from a mailbox.

        ```python
        msg = client.email.mailboxes.messages.create(
            "mbx_01krdgeqcxet5s7t44vh8rt9mg",
            to=[{"address": "user@example.com"}],
            subject="Hello",
            text="Hi there",
        )
        print(msg.id, msg.thread_id)
        ```
        """
        return self._write(
            "POST",
            f"{_PATH}/{mailbox_id}/messages",
            _compose_body(self._defaults, **kwargs),
            EmailThreadMessage,
            options,
        )


class AsyncEmailMailboxesMessages(AsyncResource):
    """Async mirror of `EmailMailboxesMessages`."""

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self._defaults = defaults

    async def create(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Compose and send an outbound message from a mailbox."""
        return await self._write(
            "POST",
            f"{_PATH}/{mailbox_id}/messages",
            _compose_body(self._defaults, **kwargs),
            EmailThreadMessage,
            options,
        )
