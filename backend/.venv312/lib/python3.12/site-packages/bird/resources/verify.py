"""The Verify product namespace: ``client.verify.verifications`` starts a
verification (sending a one-time passcode) and checks the passcode a recipient
submits.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.verify_verifications_gen import (
    AsyncVerifyVerifications,
    VerifyVerifications,
)


class Verify:
    """The Verify product namespace. Reach it via ``client.verify``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self.verifications = VerifyVerifications(client)


class AsyncVerify:
    """Async Verify namespace. Reach it via ``client.verify``."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self.verifications = AsyncVerifyVerifications(client)
