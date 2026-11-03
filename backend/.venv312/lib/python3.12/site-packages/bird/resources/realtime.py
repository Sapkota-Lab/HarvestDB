"""The Realtime channel: ``client.realtime`` — the generated publish facade plus
its nested ``channels`` and ``members`` collections, which a generated class can't
declare, and the two things that carry local crypto: end-to-end encryption for
``private-encrypted-`` channels and ``authorize_channel``.

Every Realtime operation is scoped to one Realtime app and authenticated with that
app's own credentials, sent as the ``X-Realtime-Key``/``X-Realtime-Secret`` headers
alongside the workspace bearer token. Configure them once on the client
(``Bird(realtime_key=..., realtime_secret=...)``); a call made without them raises
``BirdError`` before any request is sent.

Encrypted channels add ``realtime_encryption_master_key`` — 32 random bytes,
base64-encoded, yours alone. It never reaches Bird: a publish is sealed locally
under a per-channel key derived from it, and each subscriber gets that derived
``shared_secret`` from your own auth endpoint.
"""

from __future__ import annotations

import base64
from collections.abc import Sequence
from typing import Any, TypedDict

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._exceptions import BirdError
from bird._generated import RealtimeBatchPublishResult, RealtimePublishResult
from bird._realtime_crypto import (
    decode_master_key,
    derive_shared_secret,
    encrypt_for_channel,
    hmac_sha256_hex,
    is_encrypted_channel,
)
from bird._types import RequestOptions
from bird.resources.realtime_channels_gen import (
    AsyncRealtimeChannels,
    RealtimeChannels,
)
from bird.resources.realtime_gen import (
    AsyncRealtimeBase,
    RealtimeBase,
    RealtimeBatchEvent,
)
from bird.resources.realtime_members_gen import (
    AsyncRealtimeMembers,
    RealtimeMembers,
)

_MULTI_CHANNEL = (
    "a publish to a private-encrypted- channel must name exactly that one channel: "
    "every channel derives its own key, so a multi-channel publish would hand the "
    "other channels undecryptable ciphertext — publish per channel instead"
)
_NO_APP_CREDENTIALS = (
    "authorize_channel signs with the Realtime app credentials: pass realtime_key= "
    "and realtime_secret= when constructing the client"
)


class _ChannelAuthorizationRequired(TypedDict):
    auth: str


class ChannelAuthorization(_ChannelAuthorizationRequired, total=False):
    """What ``authorize_channel`` returns — the JSON your auth endpoint sends back to
    the browser client, field names already on the wire spelling.

    ``auth`` is always present; ``member_data`` echoes what was signed for a presence
    channel, and ``shared_secret`` carries an encrypted channel's decryption key.
    """

    member_data: str
    shared_secret: str


def _seal_data(channels: Sequence[str], data: Any, master_key: str | None) -> Any:
    """``data`` sealed for an encrypted channel, or returned untouched for plain ones."""
    encrypted = [c for c in channels if is_encrypted_channel(c)]
    if not encrypted:
        return data
    if len(channels) > 1:
        raise BirdError(_MULTI_CHANNEL)
    return encrypt_for_channel(encrypted[0], data, decode_master_key(master_key))


def _seal_events(
    events: Sequence[RealtimeBatchEvent], master_key: str | None
) -> Sequence[RealtimeBatchEvent]:
    """Each encrypted item sealed under its own channel's key. A batch event names one
    channel, so the items encrypt independently and plain ones pass through."""
    if not any(is_encrypted_channel(e["channel"]) for e in events):
        return events
    key = decode_master_key(master_key)
    return [
        {**e, "data": encrypt_for_channel(e["channel"], e.get("data"), key)}
        if is_encrypted_channel(e["channel"])
        else e
        for e in events
    ]


def _authorization(
    *,
    connection_id: str,
    channel_name: str,
    member_data: str | None,
    key: str | None,
    secret: str | None,
    master_key: str | None,
) -> ChannelAuthorization:
    if not key or not secret:
        raise BirdError(_NO_APP_CREDENTIALS)
    to_sign = f"{connection_id}:{channel_name}"
    if member_data is not None:
        to_sign = f"{to_sign}:{member_data}"
    out: ChannelAuthorization = {"auth": f"{key}:{hmac_sha256_hex(secret, to_sign)}"}
    if member_data is not None:
        out["member_data"] = member_data
    if is_encrypted_channel(channel_name):
        out["shared_secret"] = base64.b64encode(
            derive_shared_secret(channel_name, decode_master_key(master_key))
        ).decode()
    return out


class Realtime(RealtimeBase):
    """Publish to a Realtime app and inspect its live state. Reach it via ``client.realtime``."""

    def __init__(
        self,
        client: SyncAPIClient,
        realtime_key: str | None = None,
        realtime_secret: str | None = None,
        encryption_master_key: str | None = None,
    ) -> None:
        super().__init__(client)
        self.channels = RealtimeChannels(client)
        self.members = RealtimeMembers(client)
        self._realtime_key = realtime_key
        self._realtime_secret = realtime_secret
        self._encryption_master_key = encryption_master_key

    def publish(
        self,
        realtime_app_id: str,
        *,
        event: str,
        channels: Sequence[str],
        data: Any | None = None,
        exclude_connection_id: str | None = None,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimePublishResult:
        """Publish an event to a Realtime app's channels, sealing the payload
        end-to-end when the channel asks for it: a ``private-encrypted-`` channel's
        ``data`` is encrypted locally under the configured master key before the
        request leaves the process. One channel per encrypted publish — each channel
        derives its own key, so a fan-out would deliver ciphertext the other channels'
        subscribers cannot open.

        ```python
        result = client.realtime.publish(
            "rap_01krdgeqcxet5s7t44vh8rt9mg",
            event="order.updated",
            channels=["orders", "presence-lobby"],
            data={"order_id": "ord_123", "status": "shipped"},
        )
        print(result.data)
        ```

        ```python
        # End-to-end encrypted: the master key is configured on the client and the
        # payload is sealed here, so Bird only ever sees {"nonce", "ciphertext"}.
        client = Bird(
            realtime_key="rk_live_...",
            realtime_secret="rs_live_...",
            realtime_encryption_master_key="AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA=",
        )
        client.realtime.publish(
            "rap_01krdgeqcxet5s7t44vh8rt9mg",
            event="order.updated",
            channels=["private-encrypted-orders"],
            data={"order_id": "ord_123", "status": "shipped"},
        )
        ```
        """
        return super().publish(
            realtime_app_id,
            event=event,
            channels=channels,
            data=_seal_data(channels, data, self._encryption_master_key),
            exclude_connection_id=exclude_connection_id,
            include=include,
            options=options,
        )

    def publish_batch(
        self,
        realtime_app_id: str,
        *,
        events: Sequence[RealtimeBatchEvent],
        options: RequestOptions | None = None,
    ) -> RealtimeBatchPublishResult:
        """Publish up to 100 events in one call, each addressed to its own channel and
        each sealed independently when that channel is ``private-encrypted-``.

        ```python
        client.realtime.publish_batch(
            "rap_01krdgeqcxet5s7t44vh8rt9mg",
            events=[
                {"event": "order.created", "channel": "orders", "data": {"id": 1}},
                {"event": "order.updated", "channel": "private-encrypted-orders", "data": {"id": 2}},
            ],
        )
        ```
        """
        return super().publish_batch(
            realtime_app_id,
            events=_seal_events(events, self._encryption_master_key),
            options=options,
        )

    def authorize_channel(
        self, *, connection_id: str, channel_name: str, member_data: str | None = None
    ) -> ChannelAuthorization:
        """Sign a channel subscription for the browser client — the JSON body your auth
        endpoint returns. Runs locally, with no request: the signature is
        ``HMAC-SHA256(secret, "<connection_id>:<channel_name>[:<member_data>]")``,
        prefixed with the app key.

        For a presence channel pass ``member_data``, the exact JSON string carrying
        ``member_id`` (and optionally ``member_info``) — it is signed and echoed
        byte-identical, so serialize it once and pass that string. For a
        ``private-encrypted-`` channel the result also carries the channel's
        ``shared_secret``, derived from the configured encryption master key.

        ```python
        @app.post("/bird/auth")
        def bird_auth():
            body = request.get_json()
            if not may_join(session["user"], body["channel_name"]):
                abort(403)
            return client.realtime.authorize_channel(
                connection_id=body["connection_id"],
                channel_name=body["channel_name"],
            )
        ```
        """
        return _authorization(
            connection_id=connection_id,
            channel_name=channel_name,
            member_data=member_data,
            key=self._realtime_key,
            secret=self._realtime_secret,
            master_key=self._encryption_master_key,
        )


class AsyncRealtime(AsyncRealtimeBase):
    """Async mirror of `Realtime`."""

    def __init__(
        self,
        client: AsyncAPIClient,
        realtime_key: str | None = None,
        realtime_secret: str | None = None,
        encryption_master_key: str | None = None,
    ) -> None:
        super().__init__(client)
        self.channels = AsyncRealtimeChannels(client)
        self.members = AsyncRealtimeMembers(client)
        self._realtime_key = realtime_key
        self._realtime_secret = realtime_secret
        self._encryption_master_key = encryption_master_key

    async def publish(
        self,
        realtime_app_id: str,
        *,
        event: str,
        channels: Sequence[str],
        data: Any | None = None,
        exclude_connection_id: str | None = None,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimePublishResult:
        """Publish an event, sealing the payload for a ``private-encrypted-`` channel."""
        return await super().publish(
            realtime_app_id,
            event=event,
            channels=channels,
            data=_seal_data(channels, data, self._encryption_master_key),
            exclude_connection_id=exclude_connection_id,
            include=include,
            options=options,
        )

    async def publish_batch(
        self,
        realtime_app_id: str,
        *,
        events: Sequence[RealtimeBatchEvent],
        options: RequestOptions | None = None,
    ) -> RealtimeBatchPublishResult:
        """Publish a batch, sealing each ``private-encrypted-`` item independently."""
        return await super().publish_batch(
            realtime_app_id,
            events=_seal_events(events, self._encryption_master_key),
            options=options,
        )

    def authorize_channel(
        self, *, connection_id: str, channel_name: str, member_data: str | None = None
    ) -> ChannelAuthorization:
        """Sign a channel subscription — pure local crypto, so it is not a coroutine
        even on the async client (the sync mirror documents the full contract)."""
        return _authorization(
            connection_id=connection_id,
            channel_name=channel_name,
            member_data=member_data,
            key=self._realtime_key,
            secret=self._realtime_secret,
            master_key=self._encryption_master_key,
        )
