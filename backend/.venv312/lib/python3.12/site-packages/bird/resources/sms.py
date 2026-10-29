"""Use the ``client.sms`` channel to send an SMS (free text or by stored
template), read a message, and list the message log.

A send carries either ``text`` (with ``category`` and ``from_``) or a ``template``
(by id or slug, with its ``parameters``). A workspace template requires an owned
``from_``; a built-in template selects its sender and rejects ``from_``. The two
content forms are mutually exclusive.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import SMSMessage, SMSMessageBatchResponse
from bird._types import RequestOptions
from bird.resources.sms_gen import AsyncSmsBase, SmsBase
from bird.resources.sms_stats import AsyncSmsStats, SmsStats

_PATH = "/v1/sms/messages"
_BATCH_PATH = "/v1/sms/batches"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})



def _send_body(
    *,
    to: str,
    from_: str | None = None,
    text: str | None = None,
    category: str | None = None,
    template: str | None = None,
    language: str | None = None,
    parameters: Mapping[str, Any] | None = None,
    tags: Sequence[Mapping[str, str]] | None = None,
    metadata: Mapping[str, Any] | None = None,
    smart_encoding: bool | None = None,
) -> dict[str, Any]:
    # The generated send request is an anyOf(text | template) with no single
    # wrappable model, so the body is assembled as a plain dict here; unset fields
    # are dropped. ``from_`` maps to the wire field "from" (a Python keyword).
    #
    # The wire nests smart_encoding under "options", but it is a flat keyword here:
    # ``options`` on every method in this SDK is the transport RequestOptions, so a
    # second meaning would be a trap. A future send option joins it as its own keyword.
    body: dict[str, Any] = {
        "to": to,
        "from": from_,
        "text": text,
        "category": category,
        "tags": tags,
        "metadata": metadata,
    }
    if smart_encoding is not None:
        body["options"] = {"smart_encoding": smart_encoding}
    if template is not None:
        # An smt_-prefixed value is the id; anything else is the slug handle.
        tmpl: dict[str, Any] = {"id" if template.startswith("smt_") else "slug": template}
        if language is not None:
            tmpl["language"] = language
        if parameters is not None:
            tmpl["parameters"] = parameters
        body["template"] = tmpl
    return {key: value for key, value in body.items() if value is not None}


def _message_body(m: Mapping[str, Any]) -> dict[str, Any]:
    return _send_body(
        to=m["to"],
        from_=m.get("from_"),
        text=m.get("text"),
        category=m.get("category"),
        template=m.get("template"),
        language=m.get("language"),
        parameters=m.get("parameters"),
        tags=m.get("tags"),
        metadata=m.get("metadata"),
        smart_encoding=m.get("smart_encoding"),
    )


class Sms(SmsBase):
    """Send and read SMS messages. Reach it via ``client.sms``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.stats = SmsStats(client)

    def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        text: str | None = None,
        category: str | None = None,
        template: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        smart_encoding: bool | None = None,
        options: RequestOptions | None = None,
    ) -> SMSMessage:
        """Send one SMS to a single recipient. Supply either ``text`` (with a
        ``category`` and ``from_``) or a stored ``template`` (by id or slug, with
        ``parameters``). A workspace template requires an owned ``from_``; a
        built-in template selects its sender and rejects ``from_``. The API accepts
        the message for delivery. Read it back with ``get`` for the latest status.

        ```python
        msg = client.sms.send(
            from_="+15557654321",
            to="+15551234567",
            text="Your verification code is 123456.",
            category="authentication",
        )
        print(msg.id, msg.status)
        ```

        ```python
        client.sms.send(
            to="+14155550100",
            template="bird_otp_verification",
            parameters={"code": "123456"},
        )
        ```
        """
        body = _send_body(
            to=to, from_=from_, text=text, category=category, template=template,
            language=language, parameters=parameters, tags=tags, metadata=metadata,
            smart_encoding=smart_encoding,
        )
        return self._write("POST", _PATH, body, SMSMessage, options)

    def send_batch(
        self, *, messages: Sequence[Mapping[str, Any]], options: RequestOptions | None = None
    ) -> SMSMessageBatchResponse:
        """Send up to 100 independent SMS messages in one call. Each item is shaped
        like the keyword arguments of ``send``; all are validated before any queue.

        ```python
        batch = client.sms.send_batch(
            messages=[
                {
                    "from_": "+15557654321",
                    "to": "+15551111111",
                    "text": "Hi Alice!",
                    "category": "marketing",
                },
                {
                    "from_": "+15557654321",
                    "to": "+15552222222",
                    "text": "Hi Bob!",
                    "category": "marketing",
                },
            ]
        )
        for msg in batch.data:
            print(msg.id, msg.status)
        ```
        """
        body = {"messages": [_message_body(m) for m in messages]}
        response = self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return SMSMessageBatchResponse.model_validate(response.json())




class AsyncSms(AsyncSmsBase):
    """Async mirror of `Sms`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.stats = AsyncSmsStats(client)

    async def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        text: str | None = None,
        category: str | None = None,
        template: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        smart_encoding: bool | None = None,
        options: RequestOptions | None = None,
    ) -> SMSMessage:
        """Send one SMS to a single recipient (free text or by template).

        A workspace template requires an owned ``from_``; a built-in template
        selects its sender and rejects ``from_``.
        """
        body = _send_body(
            to=to, from_=from_, text=text, category=category, template=template,
            language=language, parameters=parameters, tags=tags, metadata=metadata,
            smart_encoding=smart_encoding,
        )
        return await self._write("POST", _PATH, body, SMSMessage, options)

    async def send_batch(
        self, *, messages: Sequence[Mapping[str, Any]], options: RequestOptions | None = None
    ) -> SMSMessageBatchResponse:
        """Send up to 100 independent SMS messages in one call."""
        body = {"messages": [_message_body(m) for m in messages]}
        response = await self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return SMSMessageBatchResponse.model_validate(response.json())
