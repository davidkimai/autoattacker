from __future__ import annotations

import hashlib
import random


def _payload(*parts: object) -> bytes:
    return "::".join(str(part) for part in parts).encode("utf-8")


def derive_seed(*parts: object) -> int:
    digest = hashlib.sha256(_payload(*parts)).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


def rng_for(*parts: object) -> random.Random:
    return random.Random(derive_seed(*parts))


def short_hash(*parts: object, length: int = 10) -> str:
    return hashlib.sha256(_payload(*parts)).hexdigest()[:length]
