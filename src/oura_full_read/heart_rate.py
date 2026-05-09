"""Heart-rate parsers for standard BLE HRM and Oura custom latest values."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .constants import (
    OURA_FEATURE_NAMES,
    OURA_FEATURE_REQUEST_RESULTS,
    OURA_FEATURE_STATES,
    OURA_FEATURE_STATUS_BITS,
)
from .util import to_hex


@dataclass(frozen=True)
class StandardHeartRateMeasurement:
    raw_hex: str
    heart_rate_bpm: int
    sensor_contact_supported: bool
    sensor_contact_detected: bool | None
    energy_expended: int | None
    rr_intervals_seconds: tuple[float, ...]


@dataclass(frozen=True)
class OuraHeartRateLatest:
    raw_hex: str
    source: str
    capability_id: int
    request_result: str | None
    request_result_raw: int
    status_values: tuple[str, ...]
    status_mask: int
    state: str | None
    state_raw: int
    time_since_last_measurement: int
    values: dict[str, int | float | str | None]


def as_dict(value: object) -> dict[str, object]:
    return asdict(value)


def _short_le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little", signed=True)


def _int_le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little", signed=True)


def _status_values(mask: int) -> tuple[str, ...]:
    base = "on" if mask % 2 else "off"
    return (base,) + tuple(
        name for bit, name in OURA_FEATURE_STATUS_BITS.items() if mask & (1 << bit)
    )


def parse_standard_heart_rate_measurement(data: bytes) -> StandardHeartRateMeasurement:
    if len(data) < 2:
        raise ValueError("heart-rate measurement is too short")
    flags = data[0]
    offset = 1
    if flags & 0x01:
        if len(data) < offset + 2:
            raise ValueError("heart-rate measurement missing uint16 BPM")
        heart_rate_bpm = int.from_bytes(data[offset : offset + 2], "little")
        offset += 2
    else:
        heart_rate_bpm = data[offset]
        offset += 1

    contact_bits = (flags >> 1) & 0x03
    sensor_contact_supported = contact_bits in (2, 3)
    sensor_contact_detected = None
    if sensor_contact_supported:
        sensor_contact_detected = contact_bits == 3

    energy_expended = None
    if flags & 0x08:
        if len(data) < offset + 2:
            raise ValueError("heart-rate measurement missing energy field")
        energy_expended = int.from_bytes(data[offset : offset + 2], "little")
        offset += 2

    rr_intervals = []
    if flags & 0x10:
        while offset + 1 < len(data):
            rr_raw = int.from_bytes(data[offset : offset + 2], "little")
            rr_intervals.append(rr_raw / 1024)
            offset += 2

    return StandardHeartRateMeasurement(
        raw_hex=to_hex(data),
        heart_rate_bpm=heart_rate_bpm,
        sensor_contact_supported=sensor_contact_supported,
        sensor_contact_detected=sensor_contact_detected,
        energy_expended=energy_expended,
        rr_intervals_seconds=tuple(rr_intervals),
    )


def build_oura_latest_heart_rate_request(capability_id: int) -> bytes:
    return bytes([0x2F, 0x02, 0x24, capability_id & 0xFF])


def parse_oura_latest_heart_rate_response(
    response: bytes,
    expected_capability_id: int | None = None,
) -> OuraHeartRateLatest:
    if len(response) < 9 or response[0] != 0x2F or response[2] != 0x25:
        raise ValueError(f"not an Oura latest-values response: {to_hex(response)}")
    capability_id = response[3]
    if expected_capability_id is not None and capability_id != expected_capability_id:
        raise ValueError(
            f"capability mismatch: expected {expected_capability_id}, got {capability_id}"
        )

    request_result = response[4]
    status_mask = response[5]
    state = response[6]
    time_since_last_measurement = _short_le(response, 7)
    values: dict[str, int | float | str | None]

    if capability_id == 2 and len(response) >= 18:
        rr_corrected_ibi = _short_le(response, 9)
        values = {
            "rr_corrected_ibi_ms": rr_corrected_ibi,
            "heart_rate_bpm": round(60000 / rr_corrected_ibi, 2)
            if rr_corrected_ibi > 0
            else None,
            "previous_cqi_value": _int_le(response, 11),
            "last_temperature_raw": _short_le(response, 15),
            "previous_pqi_value": response[17],
        }
    elif capability_id == 3 and len(response) >= 17:
        values = {
            "signal_quality": response[9],
            "last_acm_value": response[10],
            "acm_motion_frequency": response[11],
            "regularity": response[12],
            "last_hr_value_bpm": response[13],
            "last_hr_approximation_bpm": response[14],
            "last_temperature_raw": _short_le(response, 15),
        }
    elif capability_id == 4 and len(response) >= 16:
        values = {
            "signal_quality": response[9],
            "last_perfusion_index_red": response[10],
            "last_perfusion_index_ir": response[11],
            "last_spo2_level": response[12],
            "last_hr_level_bpm": response[13],
            "last_temperature_raw": _short_le(response, 14),
        }
    else:
        values = {"payload_hex": to_hex(response[9:])}

    return OuraHeartRateLatest(
        raw_hex=to_hex(response),
        source=OURA_FEATURE_NAMES.get(capability_id, f"unknown-{capability_id}"),
        capability_id=capability_id,
        request_result=OURA_FEATURE_REQUEST_RESULTS.get(request_result),
        request_result_raw=request_result,
        status_values=_status_values(status_mask),
        status_mask=status_mask,
        state=OURA_FEATURE_STATES.get(state),
        state_raw=state,
        time_since_last_measurement=time_since_last_measurement,
        values=values,
    )
