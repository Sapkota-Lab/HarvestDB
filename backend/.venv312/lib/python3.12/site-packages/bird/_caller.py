"""Bird-Caller detection: which agent harness drives the SDK.

Best-effort, non-authoritative usage telemetry -- it only labels traffic, never
gates behavior. The single source of truth is ``clients/caller-detection.yaml``
(shared with the CLI and the other SDKs); the ordered rule table in
``_caller_rules`` is generated from it.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

from ._caller_rules import CALLER_BOOLEANISH_SKIP, CALLER_DEFAULT, CALLER_RULES

_VALID = re.compile(r"^[a-z0-9._-]+$")


def detect_caller(environ: Mapping[str, str] | None = None) -> str:
    """Infer the driving environment by walking the generated rules in order.

    ``environ`` is injected in tests; production uses ``os.environ``.
    """
    env = os.environ if environ is None else environ
    for rule in CALLER_RULES:
        value = env.get(str(rule["env"]), "")
        equals = rule.get("equals")
        if not value or (equals is not None and value != equals):
            continue
        if not rule.get("passthrough"):
            return str(rule["name"])
        sanitized = _sanitize(value)
        if sanitized:
            return sanitized
    return CALLER_DEFAULT


def _sanitize(value: str) -> str:
    # Lowercase and bound a passthrough (AGENT=<name>) value the same charset+length
    # way as the other Bird-* labels; drop boolean-ish values with no harness identity.
    s = value.strip().lower()
    if not s or len(s) > 32 or s in CALLER_BOOLEANISH_SKIP:
        return ""
    return s if _VALID.match(s) else ""
