"""The WhatsApp channel: ``client.whatsapp`` — send a message, read one back,
list the message log, list a single message's event timeline, and reach one
message's subresources through ``client.whatsapp.messages``.

A send carries exactly one kind of content: a template, or free-form ``text``,
``image``, ``video``, ``audio``, ``sticker``, ``document``, ``location``,
``contact_cards`` or ``interactive``. Free-form content is deliverable only
inside an open 24-hour customer service window.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import WhatsAppMessage
from bird._types import RequestOptions
from bird.resources.whatsapp_gen import AsyncWhatsappBase, WhatsappBase
from bird.resources.whatsapp_business_accounts_gen import (
    AsyncWhatsappBusinessAccounts,
    WhatsappBusinessAccounts,
)
from bird.resources.whatsapp_keyword_rules_gen import (
    AsyncWhatsappKeywordRules,
    WhatsappKeywordRules,
)
from bird.resources.whatsapp_messages import AsyncWhatsappMessages, WhatsappMessages
from bird.resources.whatsapp_numbers import AsyncWhatsappNumbers, WhatsappNumbers
from bird.resources.whatsapp_reaction_gen import AsyncWhatsappReaction, WhatsappReaction
from bird.resources.whatsapp_suppressions_gen import (
    AsyncWhatsappSuppressions,
    WhatsappSuppressions,
)
from bird.resources.whatsapp_stats import AsyncWhatsappStats, WhatsappStats
from bird.resources.whatsapp_groups import AsyncWhatsappGroups, WhatsappGroups
from bird.resources.whatsapp_templates import AsyncWhatsappTemplates, WhatsappTemplates

_PATH = "/v1/whatsapp/messages"


def _send_body(
    *,
    to: str,
    from_: str | None = None,
    template: str | None = None,
    language: str | None = None,
    components: Sequence[Mapping[str, Any]] | None = None,
    text: Mapping[str, Any] | None = None,
    image: Mapping[str, Any] | None = None,
    video: Mapping[str, Any] | None = None,
    audio: Mapping[str, Any] | None = None,
    sticker: Mapping[str, Any] | None = None,
    document: Mapping[str, Any] | None = None,
    location: Mapping[str, Any] | None = None,
    interactive: Mapping[str, Any] | None = None,
    contact_cards: Sequence[Mapping[str, Any]] | None = None,
    in_reply_to_message_id: str | None = None,
    tags: Sequence[Mapping[str, str]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"to": to}
    if from_ is not None:
        body["from"] = from_
    if template is not None:
        # A wat_-prefixed value is the id; anything else is the slug handle.
        tmpl: dict[str, Any] = {"id" if template.startswith("wat_") else "slug": template}
        if language is not None:
            tmpl["language"] = language
        if components is not None:
            tmpl["components"] = components
        body["template"] = tmpl
    content: dict[str, Mapping[str, Any] | None] = {
        "text": text,
        "image": image,
        "video": video,
        "audio": audio,
        "sticker": sticker,
        "document": document,
        "location": location,
        "interactive": interactive,
    }
    for name, value in content.items():
        if value is not None:
            body[name] = value
    if contact_cards is not None:
        body["contact_cards"] = contact_cards
    if in_reply_to_message_id is not None:
        body["in_reply_to_message_id"] = in_reply_to_message_id
    if tags is not None:
        body["tags"] = tags
    if metadata is not None:
        body["metadata"] = metadata
    return body


class Whatsapp(WhatsappBase):
    """Send and read WhatsApp messages. Reach it via ``client.whatsapp``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.stats = WhatsappStats(client)
        self.messages = WhatsappMessages(client)
        self.templates = WhatsappTemplates(client)
        self.groups = WhatsappGroups(client)
        self.reaction = WhatsappReaction(client)
        self.numbers = WhatsappNumbers(client)
        self.business_accounts = WhatsappBusinessAccounts(client)
        self.keyword_rules = WhatsappKeywordRules(client)
        self.suppressions = WhatsappSuppressions(client)

    def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        text: Mapping[str, Any] | None = None,
        image: Mapping[str, Any] | None = None,
        video: Mapping[str, Any] | None = None,
        audio: Mapping[str, Any] | None = None,
        sticker: Mapping[str, Any] | None = None,
        document: Mapping[str, Any] | None = None,
        location: Mapping[str, Any] | None = None,
        interactive: Mapping[str, Any] | None = None,
        contact_cards: Sequence[Mapping[str, Any]] | None = None,
        in_reply_to_message_id: str | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send one message to a single recipient, carrying exactly one kind of
        content: a template named by its id (``wat_…``) or slug, or a free-form
        arm shaped like its wire object (``text={"body": …}``). ``interactive``
        is the arm that gives the recipient something to tap — reply buttons, a
        list menu, a link button, media cards, or a request for their location
        or contact details. ``contact_cards`` sends up to five contact cards: a
        card's ``name`` needs ``formatted_name`` plus at least one other part, and
        a ``phone_number`` in E.164 earns the card a button that opens a chat.
        Pass ``in_reply_to_message_id`` to quote an earlier message from the same
        conversation. Every send but a Bird-managed
        template needs ``from_``. The result is ``accepted``, not yet delivered
        — read it back with ``get`` or follow its timeline with ``list_events``.

        ```python
        msg = client.whatsapp.send(
            to="+31612345678",
            template="bird_otp",
            language="en",
            components=[{"type": "body", "parameters": [{"type": "text", "text": "123456"}]}],
        )
        print(msg.id, msg.status)
        ```
        """
        body = _send_body(
            to=to,
            from_=from_,
            template=template,
            language=language,
            components=components,
            text=text,
            image=image,
            video=video,
            audio=audio,
            sticker=sticker,
            document=document,
            location=location,
            interactive=interactive,
            contact_cards=contact_cards,
            in_reply_to_message_id=in_reply_to_message_id,
            tags=tags,
            metadata=metadata,
        )
        return self._write("POST", _PATH, body, WhatsAppMessage, options)


class AsyncWhatsapp(AsyncWhatsappBase):
    """Async mirror of `Whatsapp`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.stats = AsyncWhatsappStats(client)
        self.messages = AsyncWhatsappMessages(client)
        self.templates = AsyncWhatsappTemplates(client)
        self.groups = AsyncWhatsappGroups(client)
        self.reaction = AsyncWhatsappReaction(client)
        self.numbers = AsyncWhatsappNumbers(client)
        self.business_accounts = AsyncWhatsappBusinessAccounts(client)
        self.keyword_rules = AsyncWhatsappKeywordRules(client)
        self.suppressions = AsyncWhatsappSuppressions(client)

    async def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        text: Mapping[str, Any] | None = None,
        image: Mapping[str, Any] | None = None,
        video: Mapping[str, Any] | None = None,
        audio: Mapping[str, Any] | None = None,
        sticker: Mapping[str, Any] | None = None,
        document: Mapping[str, Any] | None = None,
        location: Mapping[str, Any] | None = None,
        interactive: Mapping[str, Any] | None = None,
        contact_cards: Sequence[Mapping[str, Any]] | None = None,
        in_reply_to_message_id: str | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send one WhatsApp message to a single recipient."""
        body = _send_body(
            to=to,
            from_=from_,
            template=template,
            language=language,
            components=components,
            text=text,
            image=image,
            video=video,
            audio=audio,
            sticker=sticker,
            document=document,
            location=location,
            interactive=interactive,
            contact_cards=contact_cards,
            in_reply_to_message_id=in_reply_to_message_id,
            tags=tags,
            metadata=metadata,
        )
        return await self._write("POST", _PATH, body, WhatsAppMessage, options)
