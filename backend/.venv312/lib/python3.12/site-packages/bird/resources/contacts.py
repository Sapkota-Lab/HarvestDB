"""client.contacts — the generated create/list/get/update/delete/batch facade
plus its nested ``preferences`` collection, which a generated class can't
declare on its own base."""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.contacts_gen import AsyncContactsBase, ContactsBase
from bird.resources.contacts_preferences_gen import (
    AsyncContactsPreferences,
    ContactsPreferences,
)


class Contacts(ContactsBase):
    """The workspace's contacts. Reach it via ``client.contacts``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.preferences = ContactsPreferences(client)


class AsyncContacts(AsyncContactsBase):
    """Async mirror of `Contacts`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.preferences = AsyncContactsPreferences(client)
