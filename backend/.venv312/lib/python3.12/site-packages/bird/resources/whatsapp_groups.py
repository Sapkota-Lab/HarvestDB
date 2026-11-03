"""``client.whatsapp.groups`` — the workspace's WhatsApp groups.

The generated base carries the group's own lifecycle; this wrapper exists to
nest the four families hung off a group under it, so a caller reaches them at
``client.whatsapp.groups.pins`` rather than as four more top-level resources.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.whatsapp_groups_gen import AsyncWhatsappGroupsBase, WhatsappGroupsBase
from bird.resources.whatsapp_groups_invite_link_gen import (
    AsyncWhatsappGroupsInviteLink,
    WhatsappGroupsInviteLink,
)
from bird.resources.whatsapp_groups_join_requests_gen import (
    AsyncWhatsappGroupsJoinRequests,
    WhatsappGroupsJoinRequests,
)
from bird.resources.whatsapp_groups_participants_gen import (
    AsyncWhatsappGroupsParticipants,
    WhatsappGroupsParticipants,
)
from bird.resources.whatsapp_groups_pins_gen import AsyncWhatsappGroupsPins, WhatsappGroupsPins


class WhatsappGroups(WhatsappGroupsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.invite_link = WhatsappGroupsInviteLink(client)
        self.join_requests = WhatsappGroupsJoinRequests(client)
        self.participants = WhatsappGroupsParticipants(client)
        self.pins = WhatsappGroupsPins(client)


class AsyncWhatsappGroups(AsyncWhatsappGroupsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.invite_link = AsyncWhatsappGroupsInviteLink(client)
        self.join_requests = AsyncWhatsappGroupsJoinRequests(client)
        self.participants = AsyncWhatsappGroupsParticipants(client)
        self.pins = AsyncWhatsappGroupsPins(client)
