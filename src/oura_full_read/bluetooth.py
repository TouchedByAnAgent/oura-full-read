"""Generic Bluetooth helpers backed by Bleak."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from .constants import (
    OURA_MANUFACTURER_ID,
    OURA_READ_CHARACTERISTIC_UUID,
    OURA_SERVICE_UUID,
    OURA_WRITE_CHARACTERISTIC_UUID,
    STANDARD_HR_SERVICE_UUID,
)
from .util import missing_bleak_error


@dataclass(frozen=True)
class ScanResult:
    address: str
    name: str | None
    rssi: int | None
    service_uuids: tuple[str, ...]
    is_oura: bool
    is_standard_heart_rate: bool
    manufacturer_ids: tuple[int, ...]


class BluetoothClient:
    def __init__(self, address: str, timeout: float = 20.0):
        self.address = address
        self.timeout = timeout
        self._client = None

    async def __aenter__(self) -> "BluetoothClient":
        try:
            from bleak import BleakClient
        except ImportError as exc:
            raise missing_bleak_error() from exc
        self._client = BleakClient(self.address, timeout=self.timeout)
        await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.disconnect()

    @property
    def client(self):
        if self._client is None:
            raise RuntimeError("Bluetooth client is not connected")
        return self._client

    async def list_services(self) -> list[dict[str, object]]:
        services = await self.client.get_services()
        rows: list[dict[str, object]] = []
        for service in services:
            rows.append(
                {
                    "kind": "service",
                    "uuid": str(service.uuid),
                    "description": getattr(service, "description", None),
                }
            )
            for char in service.characteristics:
                rows.append(
                    {
                        "kind": "characteristic",
                        "uuid": str(char.uuid),
                        "description": getattr(char, "description", None),
                        "properties": list(getattr(char, "properties", [])),
                    }
                )
                for descriptor in getattr(char, "descriptors", []):
                    rows.append(
                        {
                            "kind": "descriptor",
                            "uuid": str(descriptor.uuid),
                            "handle": getattr(descriptor, "handle", None),
                        }
                    )
        return rows

    async def read(self, characteristic_uuid: str) -> bytes:
        return bytes(await self.client.read_gatt_char(characteristic_uuid))

    async def write(self, characteristic_uuid: str, data: bytes, response: bool = False) -> None:
        await self.client.write_gatt_char(characteristic_uuid, data, response=response)

    async def notify(
        self,
        characteristic_uuid: str,
        callback: Callable[[bytes], None],
        seconds: float | None,
    ) -> None:
        def on_notification(_sender: object, data: bytearray) -> None:
            callback(bytes(data))

        await self.client.start_notify(characteristic_uuid, on_notification)
        try:
            if seconds is None:
                while True:
                    await asyncio.sleep(3600)
            else:
                await asyncio.sleep(seconds)
        finally:
            await self.client.stop_notify(characteristic_uuid)

    async def wait_for_oura_response(
        self,
        request: bytes,
        timeout: float = 5.0,
        write_response: bool = True,
    ) -> bytes:
        queue: asyncio.Queue[bytes] = asyncio.Queue()

        def on_notification(_sender: object, data: bytearray) -> None:
            queue.put_nowait(bytes(data))

        await self.client.start_notify(OURA_READ_CHARACTERISTIC_UUID, on_notification)
        try:
            await self.client.write_gatt_char(
                OURA_WRITE_CHARACTERISTIC_UUID,
                request,
                response=write_response,
            )
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        finally:
            await self.client.stop_notify(OURA_READ_CHARACTERISTIC_UUID)


async def scan(timeout: float = 10.0) -> list[ScanResult]:
    try:
        from bleak import BleakScanner
    except ImportError as exc:
        raise missing_bleak_error() from exc

    found: dict[str, ScanResult] = {}

    def on_detect(device: object, advertisement_data: object) -> None:
        service_uuids = tuple(
            uuid.lower() for uuid in getattr(advertisement_data, "service_uuids", ()) or ()
        )
        manufacturer_data = getattr(advertisement_data, "manufacturer_data", {}) or {}
        manufacturer_ids = tuple(sorted(int(item) for item in manufacturer_data.keys()))
        is_oura = OURA_SERVICE_UUID in service_uuids or OURA_MANUFACTURER_ID in manufacturer_ids
        is_standard_hr = STANDARD_HR_SERVICE_UUID in service_uuids
        found[str(getattr(device, "address", ""))] = ScanResult(
            address=str(getattr(device, "address", "")),
            name=getattr(device, "name", None) or getattr(advertisement_data, "local_name", None),
            rssi=getattr(advertisement_data, "rssi", None),
            service_uuids=service_uuids,
            is_oura=is_oura,
            is_standard_heart_rate=is_standard_hr,
            manufacturer_ids=manufacturer_ids,
        )

    scanner = BleakScanner(detection_callback=on_detect)
    await scanner.start()
    try:
        await asyncio.sleep(timeout)
    finally:
        await scanner.stop()
    return list(found.values())
