"""Threads: ``client.email.threads`` — the generated thread facade plus its
nested ``messages`` collection, which a generated class can't declare.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_threads_gen import AsyncEmailThreadsBase
from bird.resources.email_threads_gen import EmailThreadsBase
from bird.resources.email_threads_messages_gen import (
    AsyncEmailThreadsMessages,
    EmailThreadsMessages,
)


class EmailThreads(EmailThreadsBase):
    """Conversations across every mailbox. Reach it via ``client.email.threads``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.messages = EmailThreadsMessages(client)


class AsyncEmailThreads(AsyncEmailThreadsBase):
    """Async mirror of `EmailThreads`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.messages = AsyncEmailThreadsMessages(client)
