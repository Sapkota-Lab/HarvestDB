"""``APIResponse`` — the parsed result plus its raw HTTP response.

Returned by ``client.<resource>.with_raw_response.<method>(...)``: read transport
metadata (``status_code``, ``headers``, ``request_id``) and call ``parse()`` for
the typed model. This is the Python form of the transport-metadata escape hatch
the Go and TS SDKs expose.
"""

from __future__ import annotations

from typing import Generic, TypeVar

import httpx
import pydantic

T = TypeVar("T", bound=pydantic.BaseModel)


class APIResponse(Generic[T]):
    def __init__(self, response: httpx.Response, cast_to: type[T]) -> None:
        self.http_response = response
        self._cast_to = cast_to

    @property
    def status_code(self) -> int:
        return self.http_response.status_code

    @property
    def headers(self) -> httpx.Headers:
        return self.http_response.headers

    @property
    def request_id(self) -> str | None:
        return self.http_response.headers.get("x-request-id")

    def parse(self) -> T:
        return self._cast_to.model_validate(self.http_response.json())
