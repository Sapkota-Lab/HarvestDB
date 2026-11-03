"""Subresources of one WhatsApp message: ``client.whatsapp.messages``. The
channel's own message verbs stay on ``client.whatsapp``; this namespace holds
what a single message owns.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from bird._exceptions import APIConnectionError
from bird._resource import AsyncResource, Resource, _opts
from bird._types import RequestOptions

_PATH = "/v1/whatsapp/messages"


@dataclass(frozen=True)
class WhatsappMedia:
    """Media downloaded from a received WhatsApp message. ``content_type`` is
    what storage declared, which is the message's own ``mime_type``."""

    data: bytes
    content_type: str
    content_length: int


def _media_path(message_id: str, media_id: str) -> str:
    return f"{_PATH}/{message_id}/media/{media_id}"


def _media_from(response: httpx.Response) -> WhatsappMedia:
    data = response.content
    return WhatsappMedia(
        data=data,
        content_type=response.headers.get("Content-Type") or "application/octet-stream",
        content_length=len(data),
    )


def _media_location(response: httpx.Response) -> str:
    location = response.headers.get("Location")
    if not location:
        raise APIConnectionError("media redirect carried no Location header")
    return location


def _storage_timeout(
    options: RequestOptions | None, client_timeout: httpx.Timeout | float | None
) -> httpx.Timeout | float | None:
    # The bare client for the storage hop starts from httpx's own 5s default,
    # which is not this SDK's: a 100 MB video is a normal download here. Take
    # the call's timeout, then the client's.
    if options is not None and "timeout" in options:
        return options["timeout"]
    return client_timeout


def _storage_failed(err: Exception) -> APIConnectionError:
    # Same reason as _storage_refused: the caller recovers from every storage
    # failure the same way, and an httpx type leaking out would be the only
    # place this SDK raises one.
    return APIConnectionError(
        f"downloading media failed: {err}; call media again for a fresh link"
    )


def _storage_refused(status: int) -> APIConnectionError:
    # Never routed through from_response: a storage XML body is no Bird error
    # envelope, and a 403 mapped that way would report the caller's own key as
    # lacking permission.
    return APIConnectionError(
        f"storage refused the download link (status {status}): the link expired "
        "or was refused, call media again for a fresh link"
    )


class WhatsappMessages(Resource):
    """One message's subresources. Reach it via ``client.whatsapp.messages``."""

    def media(
        self, message_id: str, media_id: str, options: RequestOptions | None = None
    ) -> WhatsappMedia:
        """Download the media on a received WhatsApp message — an image, video,
        audio clip, sticker or document. ``media_id`` is the ``id`` on the
        message's content object, which ``client.whatsapp.get`` returns.

        Media is kept for 30 days after the message arrives; after that the
        message still lists the media's ``mime_type`` and ``caption``, and this
        raises a 410 :class:`APIStatusError`. Outbound messages carry no stored
        media.

        ```python
        media = client.whatsapp.messages.media(
            "wam_01kya19eknftrs2s6p82asmvnh", "waf_01kyb2m4xq7whs0d8n3prv6tez"
        )
        print(media.content_type, media.content_length)
        ```
        """
        response = self._client.request(
            "GET", _media_path(message_id, media_id), success_status=302, **_opts(options)
        )
        # A 2xx is an edge answering with the bytes directly, which is also the
        # only arm the conformance corpus can script — its responses carry only
        # status and body, so no 302 with a Location.
        if response.status_code != 302:
            return _media_from(response)
        location = _media_location(response)
        try:
            with httpx.Client(timeout=_storage_timeout(options, self._client.timeout)) as bare:
                stored = bare.get(location)
        except httpx.HTTPError as err:
            raise _storage_failed(err) from err
        if not stored.is_success:
            raise _storage_refused(stored.status_code)
        return _media_from(stored)


class AsyncWhatsappMessages(AsyncResource):
    """Async mirror of `WhatsappMessages`."""

    async def media(
        self, message_id: str, media_id: str, options: RequestOptions | None = None
    ) -> WhatsappMedia:
        """Download a received message's media; see :meth:`WhatsappMessages.media`."""
        response = await self._client.request(
            "GET", _media_path(message_id, media_id), success_status=302, **_opts(options)
        )
        if response.status_code != 302:
            return _media_from(response)
        location = _media_location(response)
        try:
            async with httpx.AsyncClient(
                timeout=_storage_timeout(options, self._client.timeout)
            ) as bare:
                stored = await bare.get(location)
        except httpx.HTTPError as err:
            raise _storage_failed(err) from err
        if not stored.is_success:
            raise _storage_refused(stored.status_code)
        return _media_from(stored)
