"""client.broadcasts — one piece of template content sent to a stored audience.

The reads plus ``cancel`` and ``delete`` are generated; ``create``, ``update``
and ``send`` are hand-written because each carries a ``scheduled_at`` the
generator has no wire conversion for, and ``create``/``update`` also carry a
``from`` address union.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._exceptions import BirdError
from bird._generated import (
    EmailBroadcast,
    EmailBroadcastCreateRequest,
    EmailBroadcastSendNowRequest,
    EmailBroadcastUpdateRequest,
)
from bird._models import to_wire, to_wire_exclude_unset
from bird._types import EmailAddressInput, EmailDefaults, Omit, RequestOptions, omit
from bird.resources.broadcasts_gen import AsyncBroadcastsBase, BroadcastsBase

_NAIVE_SCHEDULED_AT = (
    "scheduled_at requires a timezone-aware datetime (e.g. tzinfo=timezone.utc): "
    "the API measures the delay from now in absolute time, so an offset-less "
    "value has no defined meaning on the wire"
)


def _scheduled_at_wire(value: str | datetime | None) -> str | None:
    """RFC 3339 with an explicit offset. A string is already wire-shaped and
    passes through verbatim; a naive ``datetime`` (no ``tzinfo``) is rejected
    rather than silently assumed to be UTC. A zero offset is written ``Z``,
    which is what the conformance vectors and the other three SDKs emit --
    ``isoformat()`` alone gives ``+00:00``."""
    if not isinstance(value, datetime):
        return value
    if value.utcoffset() is None:
        raise BirdError(_NAIVE_SCHEDULED_AT)
    return value.isoformat().replace("+00:00", "Z")


# The email defaults a broadcast create accepts, derived rather than listed so a
# field added to EmailDefaults reaches it for free. Only ``from_`` is spelled
# differently on the wire, which the merge below maps.
_BROADCAST_DEFAULT_KEYS = tuple(
    k for k in EmailDefaults.__annotations__ if k in EmailBroadcastCreateRequest.model_fields
)


def _create_template(template: str | None, language: str | None) -> dict[str, Any] | None:
    # The language is one of the template's own languages, so it travels inside
    # the template reference rather than beside it.
    if template is None:
        if language is not None:
            raise ValueError("language needs a template: the language is chosen from the template it belongs to")
        return None
    nested: dict[str, Any] = {"id": template}
    if language is not None:
        nested["language"] = language
    return nested


def _create_body(
    from_: EmailAddressInput | None,
    audience_id: str | None,
    template: str | None,
    reply_to: Sequence[EmailAddressInput] | None,
    headers: Mapping[str, str] | None,
    tags: Sequence[Mapping[str, str]] | None,
    metadata: Mapping[str, Any] | None,
    track_opens: bool | None,
    track_clicks: bool | None,
    ip_pool_id: str | None,
    category: str | None,
    send: bool | None,
    scheduled_at: str | datetime | None,
    defaults: EmailDefaults | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "from": from_,
        "audience_id": audience_id,
        "template": _create_template(template, language),
        "reply_to": reply_to,
        "headers": headers,
        "tags": tags,
        "metadata": metadata,
        "track_opens": track_opens,
        "track_clicks": track_clicks,
        "ip_pool_id": ip_pool_id,
        "category": category,
        "send": send,
        "scheduled_at": _scheduled_at_wire(scheduled_at),
    }
    # A per-call value always wins; an unset field falls back to the client
    # default. Create only -- an update leaves an unset field at whatever the
    # draft holds, so a default filled there would overwrite a stored value the
    # caller never named.
    if defaults:
        for key in _BROADCAST_DEFAULT_KEYS:
            wire = "from" if key == "from_" else key
            if fields.get(wire) is None and (value := defaults.get(key)) is not None:
                fields[wire] = value
    return to_wire(EmailBroadcastCreateRequest, fields)


def _update_body(
    from_: EmailAddressInput | None,
    audience_id: str | None,
    template: str | None | Omit,
    reply_to: Sequence[EmailAddressInput] | None | Omit,
    headers: Mapping[str, str] | None,
    tags: Sequence[Mapping[str, str]] | None,
    metadata: Mapping[str, Any] | None,
    track_opens: bool | None,
    track_clicks: bool | None,
    ip_pool_id: str | None | Omit,
    category: str | None,
    language: str | None | Omit = omit,
) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if from_ is not None:
        body["from"] = from_
    if audience_id is not None:
        body["audience_id"] = audience_id
    # None clears (JSON null); omit leaves the stored value unchanged. The two
    # are distinct on the wire, so the sentinel is what separates them. Naming a
    # template releases the version the broadcast is fixed to, so a language on
    # its own is sent without an id and keeps it.
    # Clearing the template clears its language too, so ``language=None``
    # beside ``template=None`` asks for the same clear twice and goes through.
    if not isinstance(template, Omit) and template is None:
        if not isinstance(language, Omit) and language is not None:
            raise ValueError("language needs a template: the language is chosen from the template it belongs to")
        body["template"] = None
    elif not isinstance(template, Omit) or not isinstance(language, Omit):
        nested: dict[str, Any] = {}
        if not isinstance(template, Omit):
            nested["id"] = template
        if not isinstance(language, Omit):
            nested["language"] = language
        body["template"] = nested
    if not isinstance(reply_to, Omit):
        body["reply_to"] = reply_to
    if headers is not None:
        body["headers"] = headers
    if tags is not None:
        body["tags"] = tags
    if metadata is not None:
        body["metadata"] = metadata
    if track_opens is not None:
        body["track_opens"] = track_opens
    if track_clicks is not None:
        body["track_clicks"] = track_clicks
    if not isinstance(ip_pool_id, Omit):
        body["ip_pool_id"] = ip_pool_id
    if category is not None:
        body["category"] = category
    return to_wire_exclude_unset(EmailBroadcastUpdateRequest, body)


def _send_body(scheduled_at: str | datetime | None) -> dict[str, Any]:
    return to_wire(
        EmailBroadcastSendNowRequest, {"scheduled_at": _scheduled_at_wire(scheduled_at)}
    )


class Broadcasts(BroadcastsBase):
    """Broadcasts: draft, update, send, cancel, and read how one landed. Reach
    it via ``client.broadcasts``."""

    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self._defaults = defaults

    def create(
        self,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None = None,
        category: str | None = None,
        language: str | None = None,
        send: bool | None = None,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Create a broadcast. It is a draft unless ``send`` is set, in which
        case it goes out immediately, or at ``scheduled_at`` when one is given.
        A send needs a ``from_`` on a verified domain, an ``audience_id``, and a
        ``template`` with a published version; without them the call is refused
        with a ``422`` rather than saved as a draft. ``language`` selects one of
        the template's languages for the whole audience and needs ``template``;
        it has to be an exact match for a language on the published version, so
        ``fr-CA`` does not select ``fr``.

        ```python
        broadcast = client.broadcasts.create(
            from_="newsletter@example.com",
            audience_id="adn_01krdgeqcxet5s7t44vh8rt9mg",
            template="emt_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(broadcast.id, broadcast.status)
        ```
        """
        body = _create_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, send, scheduled_at,
            self._defaults, language,
        )
        return self._write("POST", "/v1/email/broadcasts", body, EmailBroadcast, options)

    def update(
        self,
        broadcast_id: str,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None | Omit = omit,
        category: str | None = None,
        language: str | None | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Change a broadcast that is still a draft or is scheduled, and return
        it as it now stands. Omitted arguments keep their current value;
        ``template``, ``language``, ``reply_to`` and ``ip_pool_id`` take
        ``None`` to clear. A broadcast that has started sending can no longer be edited
        and raises a ``409``.

        ```python
        broadcast = client.broadcasts.update(
            "eb_01krdgeqcxet5s7t44vh8rt9mg",
            template="emt_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(broadcast.status)
        ```
        """
        body = _update_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, language,
        )
        return self._write(
            "PATCH",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}",
            body,
            EmailBroadcast,
            options,
        )

    def send(
        self,
        broadcast_id: str,
        *,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Send a draft broadcast, immediately or at ``scheduled_at``. The
        broadcast needs a ``from_`` on a verified domain, an ``audience_id``,
        and a ``template`` with a published version. One that has already
        started sending or has reached a final state raises a ``409``.

        ```python
        broadcast = client.broadcasts.send("eb_01krdgeqcxet5s7t44vh8rt9mg")
        print(broadcast.status)
        ```
        """
        return self._write(
            "POST",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/send",
            _send_body(scheduled_at),
            EmailBroadcast,
            options,
        )


class AsyncBroadcasts(AsyncBroadcastsBase):
    """Async mirror of `Broadcasts`."""

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self._defaults = defaults

    async def create(
        self,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None = None,
        category: str | None = None,
        language: str | None = None,
        send: bool | None = None,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Create a broadcast. See `Broadcasts.create`."""
        body = _create_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, send, scheduled_at,
            self._defaults, language,
        )
        return await self._write("POST", "/v1/email/broadcasts", body, EmailBroadcast, options)

    async def update(
        self,
        broadcast_id: str,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None | Omit = omit,
        category: str | None = None,
        language: str | None | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Change a draft or scheduled broadcast. See `Broadcasts.update`."""
        body = _update_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, language,
        )
        return await self._write(
            "PATCH",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}",
            body,
            EmailBroadcast,
            options,
        )

    async def send(
        self,
        broadcast_id: str,
        *,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Send a draft broadcast. See `Broadcasts.send`."""
        return await self._write(
            "POST",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/send",
            _send_body(scheduled_at),
            EmailBroadcast,
            options,
        )
