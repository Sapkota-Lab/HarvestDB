"""Shared base for the generated resource facades.

A generated ``<Res>`` subclasses :class:`Resource` (sync) and ``Async<Res>``
subclasses :class:`AsyncResource`; the client handle and the request-core
helpers live here once instead of being emitted into every resource file
(the Go/TS SDKs share a resource base the same way).
"""

from __future__ import annotations

from typing import Any, Sequence, TypeVar

import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._types import RequestOptions

T = TypeVar("T", bound=pydantic.BaseModel)


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    """Per-call options as request kwargs — a plain ``dict[str, Any]`` to spread
    into ``request()``; a bare ``dict(options)`` widens the values to ``object``.

    ``credentials`` is dropped: the credential resolver consumes it, and the
    transport has no such parameter."""
    kwargs = dict(options or {})
    kwargs.pop("credentials", None)
    return kwargs


def _request_kwargs(
    options: RequestOptions | None, query: dict[str, object]
) -> dict[str, Any]:
    """Merge the built query into ``extra_query`` (dropping None-valued params),
    over any ``extra_query`` the caller passed via ``options``."""
    clean = {key: value for key, value in query.items() if value is not None}
    kwargs = _opts(options)
    kwargs["extra_query"] = {**(kwargs.get("extra_query") or {}), **clean}
    return kwargs


def _creds(
    client: object,
    options: RequestOptions | None,
    kwargs: dict[str, Any],
    schemes: Sequence[str] | None,
) -> dict[str, Any]:
    """Merge the credential headers an operation's security schemes require into
    the request kwargs. Resolved by the client, which raises before the request
    when one is unconfigured."""
    if not schemes:
        return kwargs
    headers = client.credential_headers(schemes, options)  # type: ignore[attr-defined]
    kwargs["extra_headers"] = {**(kwargs.get("extra_headers") or {}), **headers}
    return kwargs


class Resource:
    """Sync request core; reached through a generated ``<Res>`` subclass."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def _get(
        self,
        path: str,
        query: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
        schemes: Sequence[str] | None = None,
    ) -> T:
        response = self._client.request("GET", path, **_creds(self._client, options, _request_kwargs(options, query), schemes))
        return model.model_validate(response.json())

    def _write(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
        schemes: Sequence[str] | None = None,
    ) -> T:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        response = self._client.request(verb, path, body=body, **_creds(self._client, options, kwargs, schemes))
        return model.model_validate(response.json())

    def _write_none(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
        schemes: Sequence[str] | None = None,
    ) -> None:
        """A write whose success is 204 (no body): same write lifecycle as
        :meth:`_write`, but the response is discarded."""
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        self._client.request(verb, path, body=body, **_creds(self._client, options, kwargs, schemes))

    def _action(
        self,
        verb: str,
        path: str,
        model: type[T],
        options: RequestOptions | None,
        schemes: Sequence[str] | None = None,
    ) -> T:
        response = self._client.request(verb, path, **_creds(self._client, options, _opts(options), schemes))
        return model.model_validate(response.json())

    def _action_none(self, verb: str, path: str, options: RequestOptions | None, schemes: Sequence[str] | None = None) -> None:
        self._client.request(verb, path, **_creds(self._client, options, _opts(options), schemes))

    def _delete(
        self,
        path: str,
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> None:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        self._client.request("DELETE", path, **kwargs)

    def _delete_model(
        self,
        path: str,
        model: type[T],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> T:
        """A delete the caller reads back. Most answer nothing worth returning;
        one whose work finishes after the call returns the accepted state, whose
        ``last_operation`` is the only handle on it."""
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        response = self._client.request("DELETE", path, **kwargs)
        return model.model_validate(response.json())


class AsyncResource:
    """Async mirror of :class:`Resource`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def _get(
        self,
        path: str,
        query: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
        schemes: Sequence[str] | None = None,
    ) -> T:
        response = await self._client.request(
            "GET", path, **_creds(self._client, options, _request_kwargs(options, query), schemes)
        )
        return model.model_validate(response.json())

    async def _write(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
        schemes: Sequence[str] | None = None,
    ) -> T:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        response = await self._client.request(verb, path, body=body, **_creds(self._client, options, kwargs, schemes))
        return model.model_validate(response.json())

    async def _write_none(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
        schemes: Sequence[str] | None = None,
    ) -> None:
        """A write whose success is 204 (no body): same write lifecycle as
        :meth:`_write`, but the response is discarded."""
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        await self._client.request(verb, path, body=body, **_creds(self._client, options, kwargs, schemes))

    async def _action(
        self,
        verb: str,
        path: str,
        model: type[T],
        options: RequestOptions | None,
        schemes: Sequence[str] | None = None,
    ) -> T:
        response = await self._client.request(verb, path, **_creds(self._client, options, _opts(options), schemes))
        return model.model_validate(response.json())

    async def _action_none(self, verb: str, path: str, options: RequestOptions | None, schemes: Sequence[str] | None = None) -> None:
        await self._client.request(verb, path, **_creds(self._client, options, _opts(options), schemes))

    async def _delete(
        self,
        path: str,
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> None:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        await self._client.request("DELETE", path, **kwargs)

    async def _delete_model(
        self,
        path: str,
        model: type[T],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> T:
        """Async mirror of :meth:`Resource._delete_model`."""
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        response = await self._client.request("DELETE", path, **kwargs)
        return model.model_validate(response.json())
