"""Crypto for Realtime end-to-end encrypted channels (``private-encrypted-…``).

The wire contract: a channel's key is ``SHA-256(channel_name || master_key)``,
carried to clients as the base64 ``shared_secret`` in the channel-auth response;
an event's payload is an XSalsa20-Poly1305 box over the JSON-serialized data,
published as ``{"nonce": …, "ciphertext": …}`` (both base64). The master key is
the customer's alone — it is never sent to Bird.

Derivation and the channel-auth signature are stdlib ``hashlib``/``hmac``. The box
cipher is not in the stdlib, so sealing and opening need PyNaCl, imported lazily
here and declared as the ``realtime-encryption`` extra: an integration that only
authorizes channels — including encrypted ones, whose ``shared_secret`` is a plain
SHA-256 — never pays for it.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from typing import Any

from bird._exceptions import BirdError

ENCRYPTED_CHANNEL_PREFIX = "private-encrypted-"

_MASTER_KEY_BYTES = 32
_NONCE_BYTES = 24

_MISSING_EXTRA = (
    "end-to-end encryption for private-encrypted- channels needs PyNaCl, because "
    "XSalsa20-Poly1305 is not in the standard library: "
    'pip install "messagebird-sdk[realtime-encryption]"'
)


def _bindings() -> Any:
    """PyNaCl's low-level bindings, or a ``BirdError`` naming the extra to install."""
    try:
        import nacl.bindings
    except ImportError as exc:
        raise BirdError(_MISSING_EXTRA) from exc
    return nacl.bindings


def is_encrypted_channel(name: str) -> bool:
    return name.startswith(ENCRYPTED_CHANNEL_PREFIX)


def decode_master_key(master_key: str | None) -> bytes:
    """Decode and validate the configured master key: 32 bytes, base64.

    Validated here so a bad key fails with a message naming the config rather
    than as a cipher-internals error at publish time.
    """
    if not master_key:
        raise BirdError(
            "a private-encrypted- channel needs the encryption master key: pass "
            "realtime_encryption_master_key= when constructing the client — generate "
            "one as 32 random bytes, base64-encoded"
        )
    try:
        decoded = base64.b64decode(master_key, validate=True)
    except (binascii.Error, ValueError):
        decoded = b""
    if len(decoded) != _MASTER_KEY_BYTES:
        raise BirdError(
            f"realtime_encryption_master_key must be {_MASTER_KEY_BYTES} bytes, base64-encoded"
        )
    return decoded


def derive_shared_secret(channel_name: str, master_key: bytes) -> bytes:
    """``SHA-256(channel_name || master_key)`` — the channel's secretbox key."""
    return hashlib.sha256(channel_name.encode() + master_key).digest()


def seal(plaintext: bytes, nonce: bytes, key: bytes) -> bytes:
    """XSalsa20-Poly1305 secretbox seal — ``tag || cipher``, with no nonce prefix."""
    sealed: bytes = _bindings().crypto_secretbox(plaintext, nonce, key)
    return sealed


def open_box(ciphertext: bytes, nonce: bytes, key: bytes) -> bytes | None:
    """Open a sealed box, or return ``None`` when authentication fails."""
    bindings = _bindings()
    try:
        opened: bytes = bindings.crypto_secretbox_open(ciphertext, nonce, key)
    except Exception:  # nacl.exceptions.CryptoError — naming it would need PyNaCl imported
        return None
    return opened


def encrypt_for_channel(
    channel_name: str, data: Any, master_key: bytes, nonce: bytes | None = None
) -> dict[str, str]:
    """Seal an event payload for one encrypted channel into its wire envelope.

    ``nonce`` exists so the shared cross-SDK vectors can replay a fixed one;
    callers leave it unset and get 24 fresh random bytes.
    """
    key = derive_shared_secret(channel_name, master_key)
    nonce = nonce if nonce is not None else secrets.token_bytes(_NONCE_BYTES)
    plaintext = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(seal(plaintext, nonce, key)).decode(),
    }


def hmac_sha256_hex(secret: str, payload: str) -> str:
    """``hex(HMAC-SHA256(secret, payload))`` — the channel-auth signature."""
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
