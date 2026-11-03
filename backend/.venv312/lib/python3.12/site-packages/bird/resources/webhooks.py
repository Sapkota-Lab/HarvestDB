"""The webhooks resource: ``client.webhooks.unwrap`` verifies a signed event and
returns the typed, discriminated value. ``unwrap`` is synchronous on both clients
— it is pure crypto, no I/O and no transport coupling."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Mapping, cast

import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._event_types import WebhookEventType
from bird._exceptions import WebhookVerificationError, _header
from bird._generated import WebhookEvent
from bird._models import BaseModel
from bird.resources.webhooks_gen import AsyncWebhooksBase, WebhooksBase

_DEFAULT_TOLERANCE = 300  # seconds

# Event types this SDK version recognizes, sourced from the generated open-enum
# constants. A type outside this set is a future event, not a malformed one.
_KNOWN_EVENT_TYPES = frozenset(
    v for k, v in vars(WebhookEventType).items() if not k.startswith("_") and isinstance(v, str)
)


class GenericWebhookEvent(BaseModel):
    """A verified webhook event whose ``type`` this SDK version doesn't recognize.

    The webhook event vocabulary is an open enum: when the platform ships a new
    event type, an older SDK returns it — with the raw ``type``, ``timestamp``, and
    ``data`` — instead of raising, so a deployed integration keeps verifying and
    processing webhooks. ``unwrap`` still returns a :class:`WebhookEvent`; for an
    unrecognized type its ``root`` is this generic envelope, so ``event.root.type``
    and ``event.root.data`` keep working and an unhandled type lands in a switch's
    default branch.
    """

    type: str
    timestamp: str
    data: Any = None


def _verify_and_parse(
    payload: str | bytes,
    headers: Mapping[str, str],
    secret: str | None,
    tolerance: int,
) -> WebhookEvent:
    """Standard Webhooks verification (HMAC-SHA256, ``v1`` tag) over the raw body.

    Operates on the raw request bytes and never re-serializes — re-encoding would
    break the signature. Any failure raises WebhookVerificationError.
    """
    if not secret:
        raise WebhookVerificationError("no webhook secret configured; pass secret= or set it on the client")

    raw = payload if isinstance(payload, (bytes, bytearray)) else payload.encode()
    msg_id = _header(headers, "webhook-id")
    timestamp = _header(headers, "webhook-timestamp")
    signatures = _header(headers, "webhook-signature")
    if not (msg_id and timestamp and signatures):
        raise WebhookVerificationError("missing webhook-id, webhook-timestamp, or webhook-signature header")

    try:
        sent_at = int(timestamp)
    except ValueError:
        raise WebhookVerificationError("invalid webhook-timestamp") from None
    if abs(int(time.time()) - sent_at) > tolerance:
        raise WebhookVerificationError("webhook timestamp is outside the tolerance window")

    key = secret[len("whsec_"):] if secret.startswith("whsec_") else secret
    try:
        key_bytes = base64.b64decode(key)
    except ValueError:
        raise WebhookVerificationError("invalid webhook secret") from None

    signed = msg_id.encode() + b"." + timestamp.encode() + b"." + raw
    expected = base64.b64encode(hmac.new(key_bytes, signed, hashlib.sha256).digest()).decode()
    for entry in signatures.split():
        version, _, signature = entry.partition(",")
        if version == "v1" and hmac.compare_digest(signature, expected):
            # Signature is valid, so parse the body. A malformed payload surfaces
            # as WebhookVerificationError; an event type this SDK version doesn't
            # know about is returned as a GenericWebhookEvent rather than rejected,
            # so a new server event can't break an older client.
            try:
                obj = json.loads(raw)
            except ValueError as exc:
                raise WebhookVerificationError("verified webhook payload is not valid JSON") from exc
            event_type = obj.get("type") if isinstance(obj, dict) else None
            if isinstance(event_type, str) and event_type and event_type not in _KNOWN_EVENT_TYPES:
                # A future event type: wrap the raw envelope as the union's root so
                # callers read it through the same event.root.type / .data path and
                # a switch with a default branch keeps working.
                try:
                    generic = GenericWebhookEvent.model_validate(obj)
                except (ValueError, pydantic.ValidationError) as exc:
                    raise WebhookVerificationError("verified webhook payload is not a valid event") from exc
                return WebhookEvent.model_construct(root=cast(Any, generic))
            try:
                return WebhookEvent.model_validate(obj)
            except (ValueError, pydantic.ValidationError) as exc:
                raise WebhookVerificationError("verified webhook payload is not a valid event") from exc
    raise WebhookVerificationError("no matching v1 signature")


class Webhooks(WebhooksBase):
    def __init__(self, client: SyncAPIClient, secret: str | None = None) -> None:
        super().__init__(client)
        self._secret = secret

    def unwrap(self, payload: str | bytes, headers: Mapping[str, str], *, secret: str | None = None, tolerance: int = _DEFAULT_TOLERANCE) -> WebhookEvent:
        """Verify a signed webhook and return the typed event (``.root`` is the
        specific event). Pass the *raw* request body, unparsed. Raises
        ``WebhookVerificationError`` on a bad signature, stale timestamp, or
        missing headers.

        ```python
        # Pass the RAW request body (bytes) and the request headers.
        event = client.webhooks.unwrap(request.body, request.headers)
        if event.root.type == "email.delivered":
            print(event.root.data.email_id)
        ```
        """
        return _verify_and_parse(payload, headers, secret or self._secret, tolerance)


class AsyncWebhooks(AsyncWebhooksBase):
    """Async mirror of `Webhooks`. ``unwrap`` stays synchronous on both clients —
    it is pure crypto, no I/O."""

    def __init__(self, client: AsyncAPIClient, secret: str | None = None) -> None:
        super().__init__(client)
        self._secret = secret

    def unwrap(self, payload: str | bytes, headers: Mapping[str, str], *, secret: str | None = None, tolerance: int = _DEFAULT_TOLERANCE) -> WebhookEvent:
        """Verify a signed webhook and return the typed event (``.root`` is the
        specific event). Pass the *raw* request body, unparsed. Raises
        ``WebhookVerificationError`` on a bad signature, stale timestamp, or
        missing headers.

        ```python
        event = client.webhooks.unwrap(request.body, request.headers)
        if event.root.type == "email.delivered":
            ...
        ```
        """
        return _verify_and_parse(payload, headers, secret or self._secret, tolerance)
