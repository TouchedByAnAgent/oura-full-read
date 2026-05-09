"""Small utility helpers shared by the reader package."""

from __future__ import annotations


def parse_hex(value: str) -> bytes:
    cleaned = (
        value.replace("0x", "")
        .replace(":", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("_", "")
    )
    if len(cleaned) % 2:
        raise ValueError("hex input must contain an even number of digits")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise ValueError(f"invalid hex input: {value!r}") from exc


def to_hex(data: bytes) -> str:
    return data.hex()


def missing_bleak_error() -> RuntimeError:
    return RuntimeError(
        "The 'bleak' package is required for Bluetooth access. Install with: "
        "python -m pip install -e full_reader"
    )
