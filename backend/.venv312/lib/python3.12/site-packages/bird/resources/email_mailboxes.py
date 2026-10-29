"""Mailboxes: ``client.email.mailboxes`` — the generated mailbox facade plus its
nested collections (``messages``, ``receive_rules``), which a generated class
can't declare.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._types import EmailDefaults
from bird.resources.email_mailboxes_gen import AsyncEmailMailboxesBase
from bird.resources.email_mailboxes_gen import EmailMailboxesBase
from bird.resources.email_mailboxes_messages import (
    AsyncEmailMailboxesMessages,
    EmailMailboxesMessages,
)
from bird.resources.email_mailboxes_receive_rules_gen import (
    AsyncEmailMailboxesReceiveRules,
    EmailMailboxesReceiveRules,
)


class EmailMailboxes(EmailMailboxesBase):
    """Manage the workspace's mailboxes. Reach it via ``client.email.mailboxes``."""

    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self.messages = EmailMailboxesMessages(client, defaults)
        self.receive_rules = EmailMailboxesReceiveRules(client)


class AsyncEmailMailboxes(AsyncEmailMailboxesBase):
    """Async mirror of `EmailMailboxes`."""

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self.messages = AsyncEmailMailboxesMessages(client, defaults)
        self.receive_rules = AsyncEmailMailboxesReceiveRules(client)
