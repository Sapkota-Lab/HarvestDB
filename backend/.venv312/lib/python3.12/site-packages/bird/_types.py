"""Shared SDK-internal types."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence, TypedDict, Union

import httpx


# An address accepted by send() — a plain email string, an RFC 5322 mailbox string
# ("Jane Doe <jane@x.com>"), or a dict/EmailAddress object with "email" and optional "name".
EmailAddressInput = Union[str, Mapping[str, str]]


class RequestOptions(TypedDict, total=False):
    """Per-call overrides, passed as the trailing ``options`` argument of any
    resource method (the cross-SDK options object). Every key is
    optional.
    """

    extra_headers: Mapping[str, str]
    extra_query: Mapping[str, Any]
    extra_body: Mapping[str, Any]
    timeout: float | httpx.Timeout | None
    max_retries: int
    idempotency_key: str
    credentials: Mapping[str, str]
    """Per-call override for the extra credentials an operation requires, keyed by
    security scheme (``{"RealtimeKey": ..., "RealtimeSecret": ...}``). Overrides the
    client config for this call, so one client can address several apps."""


class EmailDefaults(TypedDict, total=False):
    """Workspace-wide defaults for ``client.email.send``, set on the client. A
    per-send value always wins; an unset send field falls back to its default
    (the cross-SDK channel-defaults merge). Every key is optional.
    """

    from_: EmailAddressInput
    reply_to: Sequence[EmailAddressInput]
    category: str
    track_opens: bool
    track_clicks: bool
    headers: Mapping[str, str]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]
    ip_pool_id: str


class _AttachmentRequired(TypedDict):
    filename: str
    content: str  # base64-encoded bytes


class Attachment(_AttachmentRequired, total=False):
    """A file attachment for ``client.email.send``. ``filename`` and ``content`` are
    required; ``content`` is the base64-encoded attachment bytes (the SDK does not
    encode for you) and counts against the 20 MB per-send cap. ``content_type`` is
    inferred from the filename when omitted; setting ``content_id`` renders the
    attachment inline (referenceable from the HTML body as ``cid:{content_id}``).
    """

    content_type: str
    content_id: str


# Per-method params types — the dict form of each method's keyword arguments, for
# callers who build the payload as a dict and splat it (``client.email.send(**params)``).
# Parity with Go's request struct / TS's params type. Keys mirror the
# keyword argument names (``from_``, not the wire ``from``).


class _EmailSendRequired(TypedDict):
    to: Sequence[EmailAddressInput]


class EmailSendParams(_EmailSendRequired, total=False):
    """Params for ``client.email.send``. ``to`` is required, and ``from_`` is
    required unless an ``email_defaults`` from-address is set. A send is either
    inline (``subject`` plus ``html``/``text``) or by ``template`` — with a
    template, omit ``subject``/``html``/``text`` and personalize with
    ``parameters``."""

    from_: EmailAddressInput
    subject: str
    html: str
    text: str
    template: str
    language: str
    parameters: Mapping[str, Any]
    cc: Sequence[EmailAddressInput]
    bcc: Sequence[EmailAddressInput]
    reply_to: Sequence[EmailAddressInput]
    headers: Mapping[str, str]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]
    track_opens: bool
    track_clicks: bool
    ip_pool_id: str
    category: str
    attachments: Sequence[Attachment]
    # A batch item takes this on the same terms as a single send, so one batch
    # can mix scheduled and immediate messages.
    scheduled_at: str | datetime


class _EmailSendBatchRequired(TypedDict):
    messages: Sequence[EmailSendParams]


class EmailSendBatchParams(_EmailSendBatchRequired, total=False):
    """Params for ``client.email.send_batch``. ``messages`` is required — a sequence
    of per-message params (each shaped like ``EmailSendParams``); 1–100 messages,
    all validated before any are queued. An ``email_defaults`` from-address fills an
    unset ``from_`` on each message, exactly as it does for ``send``."""


class EmailListParams(TypedDict, total=False):
    """Filters for ``client.email.list``. Every key is optional."""

    limit: int
    starting_after: str
    ending_before: str
    status: str
    tag: str
    category: str
    to: str
    from_: str


class _SmsSendRequired(TypedDict):
    to: str


class SmsSendParams(_SmsSendRequired, total=False):
    """Params for ``client.sms.send``. ``to`` is required. A send is either
    free-text (``text`` plus ``category``) or by ``template`` — with a template,
    omit ``text``/``category`` and personalize with ``parameters``. ``template``
    is the template's id (``smt_`` prefix) or its slug."""

    from_: str
    text: str
    category: str
    template: str
    language: str
    parameters: Mapping[str, Any]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]
    smart_encoding: bool


class _WhatsappSendRequired(TypedDict):
    to: str


class WhatsappSendParams(_WhatsappSendRequired, total=False):
    """Params for ``client.whatsapp.send``. ``to`` is required. A send carries
    exactly one kind of content: a ``template`` (personalized by ``language``
    and ``components``), or one free-form arm (``text``, ``image``, ``video``,
    ``audio``, ``sticker``, ``document``, ``location``) shaped like its wire
    object."""

    from_: str
    template: str
    language: str
    components: Sequence[Mapping[str, Any]]
    text: Mapping[str, Any]
    image: Mapping[str, Any]
    video: Mapping[str, Any]
    audio: Mapping[str, Any]
    sticker: Mapping[str, Any]
    document: Mapping[str, Any]
    location: Mapping[str, Any]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]


class _ContactPropertyCreateRequired(TypedDict):
    key: str
    type: str


class ContactPropertyCreateParams(_ContactPropertyCreateRequired, total=False):
    """Params for ``client.contact_properties.create``. ``key`` and ``type`` are
    required; ``type`` is one of ``"string"``, ``"number"``, ``"boolean"``."""

    fallback_value: Any


class ContactPropertyUpdateParams(TypedDict, total=False):
    """Params for ``client.contact_properties.update``. Every key is optional."""

    fallback_value: Any


class _RealtimePublishRequired(TypedDict):
    event: str
    channels: Sequence[str]


class RealtimePublishParams(_RealtimePublishRequired, total=False):
    """Params for ``client.realtime.publish``. ``event`` and ``channels`` are
    required (up to 100 channels). ``data`` is any JSON value — object, array, or
    scalar — capped at 10 KB serialized. ``exclude_connection_id`` skips the
    connection that triggered the change, and ``include`` asks for per-channel
    counts (``member_count`` presence-only, ``connection_count`` gated on the app's
    connection-counting flag)."""

    data: Any
    exclude_connection_id: str
    include: Sequence[str]


class _RealtimeBatchEventRequired(TypedDict):
    event: str
    channel: str


class RealtimeBatchEventParams(_RealtimeBatchEventRequired, total=False):
    """One event inside ``client.realtime.publish_batch``. Unlike ``publish``, a
    batch event targets a single ``channel``."""

    data: Any
    exclude_connection_id: str
    include: Sequence[str]


class _RealtimePublishBatchRequired(TypedDict):
    events: Sequence[RealtimeBatchEventParams]


class RealtimePublishBatchParams(_RealtimePublishBatchRequired, total=False):
    """Params for ``client.realtime.publish_batch``. ``events`` is required — 1 to
    10 events, all validated before any is delivered."""


class RealtimeChannelsListParams(TypedDict, total=False):
    """Filters for ``client.realtime.channels.list``. Every key is optional. This
    read is a live snapshot, not a paginated collection, so there is no cursor."""

    prefix: str
    include: Sequence[str]


class RealtimeChannelGetParams(TypedDict, total=False):
    """Query params for ``client.realtime.channels.get``. Every key is optional."""

    include: Sequence[str]


class _PreferenceCreateRequired(TypedDict):
    channel: str
    handle: str
    status: str


class PreferenceCreateParams(_PreferenceCreateRequired, total=False):
    """Params for ``client.preferences.create``. ``channel``, ``handle``, and
    ``status`` are required. ``consented_at`` accepts a timezone-aware
    ``datetime`` (serialized to RFC 3339) or an already-wire string."""

    coverage: str
    sender_scope: str
    source: str
    consented_at: Union[str, datetime]


class BroadcastCreateParams(TypedDict, total=False):
    """Params for ``client.broadcasts.create``. Every key is optional on a draft;
    a send needs ``from_``, ``audience_id``, and a ``template`` with a published
    version. ``language`` selects one of that template's published languages
    for the whole audience. ``scheduled_at`` accepts a timezone-aware
    ``datetime`` (serialized to RFC 3339) or an already-wire string, and is only
    meaningful alongside ``send``."""

    from_: EmailAddressInput
    audience_id: str
    template: str
    language: str
    reply_to: Sequence[EmailAddressInput]
    headers: Mapping[str, str]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]
    track_opens: bool
    track_clicks: bool
    ip_pool_id: str
    category: str
    send: bool
    scheduled_at: Union[str, datetime]


class BroadcastUpdateParams(TypedDict, total=False):
    """Params for ``client.broadcasts.update`` (the broadcast id is positional).
    An absent key keeps the stored value; ``template``, ``language``,
    ``reply_to`` and ``ip_pool_id`` present with ``None`` clear it, which is why
    those four are the nullable ones. A ``language`` needs a ``template`` to
    belong to, so clearing the template clears the language with it."""

    from_: EmailAddressInput
    audience_id: str
    template: str | None
    language: str | None
    reply_to: Sequence[EmailAddressInput] | None
    headers: Mapping[str, str]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]
    track_opens: bool
    track_clicks: bool
    ip_pool_id: str | None
    category: str


class BroadcastSendParams(TypedDict, total=False):
    """Params for ``client.broadcasts.send`` (the broadcast id is positional).
    ``scheduled_at`` accepts a timezone-aware ``datetime`` or an already-wire
    string; omit it to send straight away."""

    scheduled_at: Union[str, datetime]


class Omit:
    """Sentinel for an argument the caller left unset, distinct from an explicit
    ``None``: a value sets it, ``None`` sends JSON ``null`` (clearing a nullable
    field), and ``omit`` (the default) leaves it out of the request entirely.
    Falsy so ``if not x`` reads naturally. Matches the reference SDKs
    (openai-python / anthropic-sdk-python).
    """

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "omit"


omit = Omit()

Headers = Mapping[str, str]
Query = Mapping[str, Any]
Body = Any
