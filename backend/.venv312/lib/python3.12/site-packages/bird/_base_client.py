"""The request lifecycle shared by the sync and async clients.

``BaseClient`` owns header assembly (SDK-owned headers always win), retries with
jittered backoff that honors ``Retry-After``, a per-attempt timeout, and the
once-and-reuse idempotency key for mutations — generated once per logical call so
a retried write never double-applies. ``SyncAPIClient`` and
``AsyncAPIClient`` add the transport loop; a resource method calls ``request()``
and never implements retries itself.
"""

from __future__ import annotations

import asyncio
import platform
import random
import time
import uuid
from typing import Any, Mapping, Sequence, TypeVar
from urllib.parse import urlsplit

import httpx

from bird._caller import detect_caller
from bird._constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, INITIAL_RETRY_DELAY, MAX_RETRY_DELAY
from bird._exceptions import BirdError, APIConnectionError, APITimeoutError, MissingAPIKeyError, from_response, parse_retry_after
from bird._types import omit, Omit
from bird._version import __version__

USER_AGENT = f"bird-sdk-python/{__version__} ({platform.python_implementation().lower()}/{platform.python_version()})"

# Bird-* client-identity headers: the API attributes the SDK
# surface from these, not the User-Agent. Telemetry labels only; computed once.
# Keys use the canonical wire casing (matching the Go/TS SDKs).
_CLIENT_HEADERS = {
    "Bird-Surface": "sdk-python",
    "Bird-Version": __version__,
    "Bird-Lang": platform.python_implementation().lower(),
    "Bird-Os": platform.system().lower(),
    "Bird-Arch": platform.machine().lower(),
}
# Bird-Caller (the driving agent harness) — omitted when no agent env is present.
_caller = detect_caller()
if _caller:
    _CLIENT_HEADERS["Bird-Caller"] = _caller

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# SDK-owned headers a caller's extra_headers must never override. Derived from
# _CLIENT_HEADERS so the two can't drift; matched case-insensitively.
_RESERVED_HEADERS = {"authorization", "user-agent", "x-bird-api-version", "idempotency-key"} | {
    key.lower() for key in _CLIENT_HEADERS
}

# Bound to the concrete client so `with`/`async with` preserve the subclass type
# (e.g. `with Bird(...) as c` keeps `c` typed as Bird, not SyncAPIClient).
_SyncClientT = TypeVar("_SyncClientT", bound="SyncAPIClient")
_AsyncClientT = TypeVar("_AsyncClientT", bound="AsyncAPIClient")


def _validate_request_path(base_url: str, path: str) -> None:
    """Reject a caller path that would move the API key off the configured origin.

    The verb-method escape hatch joins ``path`` onto ``base_url`` and then attaches
    the bearer token, so an unvalidated path can redirect the key to another host —
    ``//host``, ``user@host``, an absolute URL, or a bare-relative segment. Require a
    single leading slash and assert the resolved origin equals the base-URL origin.
    """
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError(f"request path must be an absolute path starting with a single '/': got {path!r}")
    base = urlsplit(base_url)
    full = urlsplit(base_url + path)
    if (full.scheme, full.netloc) != (base.scheme, base.netloc):
        raise ValueError(
            f"request path {path!r} must stay on the configured Bird API origin {base.scheme}://{base.netloc}"
        )


class BaseClient:
    def __init__(
        self,
        *,
        base_url: str | None,
        api_key: str | None,
        api_version: str | None = None,
        timeout: httpx.Timeout | float | None | Omit = omit,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, Any] | None = None,
        credentials: Mapping[str, tuple[str, str | None, str]] | None = None,
    ) -> None:
        # Extra credentials some operations require on top of the API key, keyed by
        # the security scheme that names them: {scheme: (header, value, how)}.
        self._credentials = dict(credentials or {})
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_key = api_key
        self.api_version = api_version
        self.max_retries = max_retries
        self.timeout: httpx.Timeout | float | None = DEFAULT_TIMEOUT if isinstance(timeout, Omit) else timeout
        self._default_headers = dict(default_headers or {})
        self._default_query = dict(default_query or {})

    def _headers(self, extra_headers: Mapping[str, str] | None, idempotency_key: str | None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        headers.update(self._default_headers)
        for key, value in (extra_headers or {}).items():
            if key.lower() not in _RESERVED_HEADERS:
                headers[key] = value
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["User-Agent"] = USER_AGENT
        headers.update(_CLIENT_HEADERS)
        if self.api_version:
            headers["X-Bird-API-Version"] = self.api_version
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _build_request(
        self,
        client: httpx.Client | httpx.AsyncClient,
        method: str,
        path: str,
        *,
        body: Any,
        extra_headers: Mapping[str, str] | None,
        extra_query: Mapping[str, Any] | None,
        extra_body: Mapping[str, Any] | None,
        timeout: httpx.Timeout | float | None | Omit,
        idempotency_key: str | None,
    ) -> httpx.Request:
        # A keyless (receiver-only) client also carries no base URL; the missing
        # API key is the caller's actionable error, so it is raised first.
        if not self.api_key or self.base_url is None:
            raise MissingAPIKeyError(
                "this client has no API key (webhook verification only); "
                "pass api_key= or set BIRD_API_KEY to call the API"
            )
        _validate_request_path(self.base_url, path)
        if extra_body:
            body = {**(body or {}), **extra_body}
        query = {**self._default_query, **(extra_query or {})}
        query = {key: value for key, value in query.items() if not isinstance(value, Omit)}
        return client.build_request(
            method,
            self.base_url + path,
            json=body,
            params=query or None,
            headers=self._headers(extra_headers, idempotency_key),
            timeout=self.timeout if isinstance(timeout, Omit) else timeout,
        )

    @staticmethod
    def _should_retry(response: httpx.Response) -> bool:
        # 409 is a semantic conflict a retry cannot resolve; 501 is not implemented.
        code = response.status_code
        return code == 429 or (500 <= code < 600 and code != 501)

    def _retry_delay(self, attempt: int, response: httpx.Response | None) -> float:
        if response is not None:
            advised = parse_retry_after(response.headers)
            if advised is not None:
                return min(advised, MAX_RETRY_DELAY)
        delay = min(INITIAL_RETRY_DELAY * 2**attempt, MAX_RETRY_DELAY)
        return delay * (1.0 + random.random() * 0.25)

    @staticmethod
    def _idempotency_key(method: str, given: str | None) -> str | None:
        if given is not None:
            return given
        return str(uuid.uuid4()) if method.upper() in _MUTATING_METHODS else None


    def credential_headers(
        self, schemes: Sequence[str] | None, options: Mapping[str, Any] | None = None
    ) -> dict[str, str]:
        """Resolve the credential headers an operation's security schemes require.

        Raises before the request when one is unconfigured, so a caller gets a named
        error instead of a 401. A per-call ``credentials`` mapping in ``options``
        overrides the client config, so one client can address several apps.
        """
        if not schemes:
            return {}
        override = (options or {}).get("credentials") or {}
        out: dict[str, str] = {}
        for scheme in schemes:
            cred = self._credentials.get(scheme)
            if cred is None:
                raise BirdError(f"unknown credential scheme {scheme!r}")
            header, value, how = cred
            # Only an ABSENT override falls back to the client config. An explicit
            # empty one is a caller error, not a request for the client's value —
            # falling back there would mix one app's key with another's secret.
            supplied = override.get(scheme)
            resolved = value if supplied is None else supplied
            if not resolved:
                raise BirdError(f"{header} is required for this operation: {how}")
            out[header] = resolved
        return out


class SyncAPIClient(BaseClient):
    def __init__(self, *, http_client: httpx.Client | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Own (and close) the client only when we created it. A client shared in via
        # with_options() or injected by the caller is theirs to close.
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_query: Mapping[str, Any] | None = None,
        extra_body: Mapping[str, Any] | None = None,
        timeout: httpx.Timeout | float | None | Omit = omit,
        idempotency_key: str | None = None,
        max_retries: int | None = None,
        success_status: int | None = None,
    ) -> httpx.Response:
        """``success_status`` is a 3xx an operation answers on success. Set only
        where the contract is a redirect the caller must take itself, because the
        target is pre-authorized and must not receive this client's credentials."""
        request = self._build_request(
            self._client, method, path,
            body=body, extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body,
            timeout=timeout, idempotency_key=self._idempotency_key(method, idempotency_key),
        )
        retries_left = self.max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            last: httpx.Response | None = None
            try:
                response = self._client.send(request)
            except httpx.TimeoutException as exc:
                if retries_left <= 0:
                    raise APITimeoutError() from exc
            except httpx.HTTPError as exc:
                if retries_left <= 0:
                    raise APIConnectionError() from exc
            else:
                if response.is_success or response.status_code == success_status:
                    return response
                if retries_left <= 0 or not self._should_retry(response):
                    raise from_response(response.status_code, response.content, response.headers)
                response.close()
                last = response
            time.sleep(self._retry_delay(attempt, last))
            retries_left -= 1
            attempt += 1

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self: _SyncClientT) -> _SyncClientT:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncAPIClient(BaseClient):
    def __init__(self, *, http_client: httpx.AsyncClient | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Own (and close) the client only when we created it. A client shared in via
        # with_options() or injected by the caller is theirs to close.
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient()

    async def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_query: Mapping[str, Any] | None = None,
        extra_body: Mapping[str, Any] | None = None,
        timeout: httpx.Timeout | float | None | Omit = omit,
        idempotency_key: str | None = None,
        max_retries: int | None = None,
        success_status: int | None = None,
    ) -> httpx.Response:
        """``success_status`` is a 3xx an operation answers on success. Set only
        where the contract is a redirect the caller must take itself, because the
        target is pre-authorized and must not receive this client's credentials."""
        request = self._build_request(
            self._client, method, path,
            body=body, extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body,
            timeout=timeout, idempotency_key=self._idempotency_key(method, idempotency_key),
        )
        retries_left = self.max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            last: httpx.Response | None = None
            try:
                response = await self._client.send(request)
            except httpx.TimeoutException as exc:
                if retries_left <= 0:
                    raise APITimeoutError() from exc
            except httpx.HTTPError as exc:
                if retries_left <= 0:
                    raise APIConnectionError() from exc
            else:
                if response.is_success or response.status_code == success_status:
                    return response
                if retries_left <= 0 or not self._should_retry(response):
                    raise from_response(response.status_code, response.content, response.headers)
                await response.aclose()
                last = response
            await asyncio.sleep(self._retry_delay(attempt, last))
            retries_left -= 1
            attempt += 1

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self: _AsyncClientT) -> _AsyncClientT:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
