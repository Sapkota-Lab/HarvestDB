"""Cursor-paginated, auto-advancing page iterators.

A list method returns a page that holds the first page's ``data`` and, when
iterated, transparently fetches the rest: ``for msg in client.email.list()`` /
``async for msg in client.email.list()``. The async page is also awaitable —
``page = await client.email.list()`` gives the first page for cursor-level control,
mirroring the sync eager fetch. ``next_cursor`` from each response is sent back as
``starting_after`` to advance. Per-call options thread through every
page request.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, AsyncIterator, Generator, Generic, Iterator, TypeVar

import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._exceptions import BirdError
from bird._types import RequestOptions, omit

T = TypeVar("T", bound=pydantic.BaseModel)


def _request_kwargs(
    options: RequestOptions | None, query: dict[str, object], cursor: str | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean = {key: value for key, value in query.items() if value is not None}
    kwargs: dict[str, Any] = dict(options or {})
    # `credentials` is consumed by the credential resolver, not the transport, which
    # has no such parameter. Mirrors _resource._opts.
    kwargs.pop("credentials", None)
    kwargs["extra_query"] = {**(kwargs.get("extra_query") or {}), **clean}
    if body is not None:
        page_body = {**body, **(kwargs.pop("extra_body", None) or {})}
        if cursor is not None:
            page_body.pop("ending_before", None)
            page_body["starting_after"] = cursor
            kwargs.pop("idempotency_key", None)
            if kwargs.get("extra_headers"):
                kwargs["extra_headers"] = {
                    key: value for key, value in kwargs["extra_headers"].items()
                    if key.lower() != "idempotency-key"
                }
        kwargs["body"] = page_body
    elif cursor is not None:
        kwargs["extra_query"]["ending_before"] = omit
        kwargs["extra_query"]["starting_after"] = cursor
    return kwargs


class SyncPage(Generic[T]):
    def __init__(
        self,
        client: SyncAPIClient,
        path: str,
        query: dict[str, object],
        item: type[T],
        options: RequestOptions | None = None,
        *,
        method: str = "GET",
        body: dict[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._path = path
        self._query = query
        self._item = item
        self._options = options
        self._method = method
        self._body = deepcopy(body)
        self.response: dict[str, Any] | None = None
        self.data, self.next_cursor = self._fetch(query)

    def _fetch(self, query: dict[str, object], cursor: str | None = None) -> tuple[list[T], str | None]:
        body = self._client.request(self._method, self._path, **_request_kwargs(self._options, query, cursor, self._body)).json()
        if self.response is None:
            self.response = body
        return [self._item.model_validate(row) for row in body.get("data", [])], body.get("next_cursor")

    def has_next_page(self) -> bool:
        return self.next_cursor is not None

    def __iter__(self) -> Iterator[T]:
        data, cursor = self.data, self.next_cursor
        while True:
            yield from data
            if cursor is None:
                return
            data, cursor = self._fetch(self._query, cursor)


class AsyncPage(Generic[T]):
    """Awaitable and async-iterable. ``async for x in client.email.list()`` iterates
    every page; ``await client.email.list()`` returns the loaded first page."""

    def __init__(
        self,
        client: AsyncAPIClient,
        path: str,
        query: dict[str, object],
        item: type[T],
        options: RequestOptions | None = None,
        *,
        method: str = "GET",
        body: dict[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._path = path
        self._query = query
        self._item = item
        self._options = options
        self._method = method
        self._body = deepcopy(body)
        self.response: dict[str, Any] | None = None
        self._loaded = False
        self.data: list[T] = []
        self.next_cursor: str | None = None

    async def _fetch(self, query: dict[str, object], cursor: str | None = None) -> tuple[list[T], str | None]:
        body = (await self._client.request(self._method, self._path, **_request_kwargs(self._options, query, cursor, self._body))).json()
        if self.response is None:
            self.response = body
        return [self._item.model_validate(row) for row in body.get("data", [])], body.get("next_cursor")

    async def _load_first(self) -> AsyncPage[T]:
        # Idempotent: the first page is fetched once and cached, so awaiting the
        # page and iterating it (in either order, or repeatedly) never re-fetches.
        if not self._loaded:
            self.data, self.next_cursor = await self._fetch(self._query)
            self._loaded = True
        return self

    def __await__(self) -> Generator[Any, None, AsyncPage[T]]:
        return self._load_first().__await__()

    def has_next_page(self) -> bool:
        # next_cursor is unknown until the first page loads. An async page can't fetch
        # in __init__, so this is meaningful only after the page is awaited or iterated;
        # raising beats silently answering "no more pages" on an unloaded page.
        if not self._loaded:
            raise BirdError("await or iterate the page before calling has_next_page()")
        return self.next_cursor is not None

    async def __aiter__(self) -> AsyncIterator[T]:
        await self._load_first()
        data, cursor = self.data, self.next_cursor
        while True:
            for row in data:
                yield row
            if cursor is None:
                return
            data, cursor = await self._fetch(self._query, cursor)
