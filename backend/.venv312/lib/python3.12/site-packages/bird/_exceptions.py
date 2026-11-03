"""The SDK's error model: a typed exception hierarchy and the single wire-to-error map.

Catch ``BirdError`` for anything the SDK raises. ``APIError`` is every failure that
originates from issuing a request — both transport failures with no HTTP response
(``APIConnectionError`` / ``APITimeoutError``) and HTTP status errors
(``APIStatusError`` and its subclasses), so ``except APIError`` catches a timeout or
connection reset alongside a 500. ``APIStatusError`` carries the HTTP ``status_code``;
branch on its ``type`` (the categories in ``ErrorType``) or catch
``RateLimitError`` / ``ValidationError`` for the extra data they carry. A bad webhook
signature is ``WebhookVerificationError`` — it happens after a 200, so it is not an
``APIError``.
"""

from __future__ import annotations

import datetime
import email.utils
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ErrorType(str, Enum):
    """The coarse error category clients branch on."""

    bad_request = "bad_request_error"
    auth = "auth_error"
    billing = "billing_error"
    permission = "permission_error"
    not_found = "not_found_error"
    conflict = "conflict_error"
    precondition = "precondition_error"
    payload_too_large = "payload_too_large_error"
    misdirected = "misdirected_error"
    validation = "validation_error"
    rate_limit = "rate_limit_error"
    internal = "internal_error"
    not_implemented = "not_implemented_error"
    service_unavailable = "service_unavailable_error"


@dataclass(frozen=True)
class ErrorDetail:
    """One per-field validation failure."""

    param: str
    message: str


@dataclass(frozen=True)
class NextAction:
    """One recovery step the server suggests. Read ``kind`` before ``operation``:
    only an ``operation`` step carries one.

    ``kind`` is ``operation`` (call the operation named in ``operation``, then read
    again), ``external`` (act somewhere this API does not reach), ``wait`` (read
    again later) or ``terminal`` (nothing resolves this, so stop retrying). A value
    this SDK version does not know is display-only: show ``description`` and offer
    no action."""

    kind: str
    description: str
    operation: str | None = None
    params: Mapping[str, str] | None = None
    url: str | None = None




class BirdError(Exception):
    """Base class for every error raised by the SDK."""


class MissingAPIKeyError(BirdError):
    """An API call on a client constructed without an API key (a receiver-only
    client, which can still ``unwrap`` webhooks). Raised before any request."""


class APIError(BirdError):
    """Base for every error that originates from issuing a request.

    Covers both transport failures with no HTTP response (``APIConnectionError`` /
    ``APITimeoutError``) and HTTP status errors (``APIStatusError`` and below), so a
    single ``except APIError`` handles anything that can go wrong on a request. Catch
    ``BirdError`` to also cover a bad webhook signature.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class APIConnectionError(APIError):
    """A network-level failure with no HTTP response (DNS, refused, reset)."""

    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    """A single attempt exceeded its timeout."""

    def __init__(self, message: str = "Request timed out.") -> None:
        super().__init__(message)


class APIStatusError(APIError):
    """An error returned by the Bird API, carrying its HTTP status — the base for
    every server-side failure.

    Branch on ``type`` for the coarse category, or catch ``RateLimitError`` /
    ``ValidationError`` for the extra data they carry. ``request_id`` correlates
    with the ``X-Request-Id`` response header — the fastest way to get support help.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        type: str,
        code: str | None = None,
        name: str | None = None,
        doc_url: str | None = None,
        request_id: str | None = None,
        param: str | None = None,
        vendor_code: str | None = None,
        remediation: str | None = None,
        next: list[NextAction] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.type = type
        self.code = code
        self.name = name
        self.doc_url = doc_url
        self.request_id = request_id
        self.param = param
        self.vendor_code = vendor_code
        self.remediation = remediation
        self.next = next or []

    def __str__(self) -> str:
        return f"{self.message} (status {self.status_code}, type {self.type}, request_id {self.request_id})"


class RateLimitError(APIStatusError):
    """A 429. ``retry_after`` is the server-advised wait in seconds, or ``None``."""

    def __init__(self, *args: Any, retry_after: float | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


class ValidationError(APIStatusError):
    """A 422. ``details`` carries the per-field failures."""

    def __init__(self, *args: Any, details: list[ErrorDetail] | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.details = details or []


class WebhookVerificationError(BirdError):
    """A webhook payload failed signature verification — a bad signature, a stale
    timestamp, or malformed headers. It happens after a 200, so it carries no HTTP
    status and is not an ``APIError``."""


_STATUS_TYPES: dict[int, ErrorType] = {
    400: ErrorType.bad_request,
    401: ErrorType.auth,
    402: ErrorType.billing,
    403: ErrorType.permission,
    404: ErrorType.not_found,
    409: ErrorType.conflict,
    412: ErrorType.precondition,
    413: ErrorType.payload_too_large,
    421: ErrorType.misdirected,
    422: ErrorType.validation,
    428: ErrorType.precondition,
    429: ErrorType.rate_limit,
    501: ErrorType.not_implemented,
    503: ErrorType.service_unavailable,
}


def _infer_type(status_code: int) -> str:
    """Map a status to a type for error bodies that carry none."""
    fallback = ErrorType.internal if status_code >= 500 else ErrorType.bad_request
    return _STATUS_TYPES.get(status_code, fallback)


def _header(headers: Mapping[str, str], name: str) -> str | None:
    """Case-insensitive header lookup."""
    name_lower = name.lower()
    for key, value in headers.items():
        if key.lower() == name_lower:
            return value
    return None


def from_response(status_code: int, body: bytes | str, headers: Mapping[str, str]) -> APIStatusError:
    """Turn a terminal non-2xx response into a typed error — the single place a wire
    error becomes an exception. The API wraps errors as ``{"error": {...}}``; a bare
    top-level body and a non-JSON body are both tolerated."""
    data: dict[str, Any] = {}
    try:
        parsed = json.loads(body)
    except (ValueError, TypeError):
        parsed = None
    if isinstance(parsed, dict):
        inner = parsed.get("error")
        data = inner if isinstance(inner, dict) else parsed

    type_ = data.get("type") or _infer_type(status_code)
    request_id = data.get("request_id") or _header(headers, "X-Request-Id")
    message = data.get("message") or f"request failed with status {status_code}"
    common: dict[str, Any] = {
        "status_code": status_code,
        "type": type_,
        "code": data.get("code"),
        "name": data.get("name"),
        "doc_url": data.get("doc_url"),
        "request_id": request_id,
        "param": data.get("param"),
        "vendor_code": data.get("vendor_code"),
        "remediation": data.get("remediation"),
        "next": [
            NextAction(
                kind=n.get("kind", ""),
                description=n.get("description", ""),
                operation=n.get("operation"),
                params=n.get("params"),
                url=n.get("url"),
            )
            for n in (data.get("next") or [])  # `or []` handles both an absent key and an explicit null
            if isinstance(n, dict)
        ],
    }

    if type_ == ErrorType.rate_limit:
        return RateLimitError(message, retry_after=parse_retry_after(headers), **common)
    if type_ == ErrorType.validation:
        details = [
            ErrorDetail(param=d.get("param", ""), message=d.get("message", ""))
            for d in data.get("details", [])
            if isinstance(d, dict)
        ]
        return ValidationError(message, details=details, **common)
    return APIStatusError(message, **common)


def parse_retry_after(headers: Mapping[str, str]) -> float | None:
    """Read a ``Retry-After`` header (delta-seconds or HTTP-date) as seconds. A
    negative or unparseable value returns ``None`` — a negative wait is meaningless."""
    value = _header(headers, "Retry-After")
    if not value:
        return None
    try:
        seconds = float(int(value))
    except ValueError:
        try:
            when = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        seconds = (when - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    return seconds if seconds >= 0 else None
