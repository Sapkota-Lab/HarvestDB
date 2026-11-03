from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.voice_caller_ids_gen import AsyncVoiceCallerIds, VoiceCallerIds
from bird.resources.voice_destinations_gen import AsyncVoiceDestinations, VoiceDestinations
from bird.resources.voice_calls_gen import AsyncVoiceCalls, VoiceCalls
from bird.resources.voice_legs_gen import AsyncVoiceLegs, VoiceLegs
from bird.resources.voice_numbers_gen import AsyncVoiceNumbers, VoiceNumbers
from bird.resources.voice_session_credentials_gen import (
    AsyncVoiceSessionCredentials,
    VoiceSessionCredentials,
)
from bird.resources.voice_trunks import AsyncVoiceTrunks, VoiceTrunks


class Voice:
    def __init__(self, client: SyncAPIClient) -> None:
        self.legs = VoiceLegs(client)
        self.trunks = VoiceTrunks(client)
        self.numbers = VoiceNumbers(client)
        self.caller_ids = VoiceCallerIds(client)
        self.destinations = VoiceDestinations(client)
        self.session_credentials = VoiceSessionCredentials(client)
        self.calls = VoiceCalls(client)


class AsyncVoice:
    def __init__(self, client: AsyncAPIClient) -> None:
        self.legs = AsyncVoiceLegs(client)
        self.trunks = AsyncVoiceTrunks(client)
        self.numbers = AsyncVoiceNumbers(client)
        self.caller_ids = AsyncVoiceCallerIds(client)
        self.destinations = AsyncVoiceDestinations(client)
        self.session_credentials = AsyncVoiceSessionCredentials(client)
        self.calls = AsyncVoiceCalls(client)
