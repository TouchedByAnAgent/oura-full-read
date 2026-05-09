"""CLI for full Bluetooth and heart-rate reading."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict

from .bluetooth import BluetoothClient, scan
from .constants import (
    OURA_FEATURE_CAPABILITIES,
    STANDARD_HR_MEASUREMENT_UUID,
)
from .heart_rate import (
    as_dict,
    build_oura_latest_heart_rate_request,
    parse_oura_latest_heart_rate_response,
    parse_standard_heart_rate_measurement,
)
from .util import parse_hex, to_hex


def print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


async def scan_command(args: argparse.Namespace) -> None:
    rows = [asdict(item) for item in await scan(timeout=args.timeout)]
    if args.oura_only:
        rows = [row for row in rows if row["is_oura"]]
    if args.heart_rate_only:
        rows = [row for row in rows if row["is_standard_heart_rate"]]
    print_json(rows)


async def services_command(args: argparse.Namespace) -> None:
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        print_json(await client.list_services())


async def read_command(args: argparse.Namespace) -> None:
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        data = await client.read(args.characteristic)
    print_json({"characteristic": args.characteristic, "hex": to_hex(data)})


async def write_command(args: argparse.Namespace) -> None:
    data = parse_hex(args.hex)
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        await client.write(args.characteristic, data, response=args.with_response)
    print_json(
        {
            "characteristic": args.characteristic,
            "sent_hex": to_hex(data),
            "with_response": args.with_response,
        }
    )


async def notify_command(args: argparse.Namespace) -> None:
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        def show(data: bytes) -> None:
            print_json({"characteristic": args.characteristic, "hex": to_hex(data)})

        await client.notify(args.characteristic, show, seconds=args.seconds)


async def hr_standard_command(args: argparse.Namespace) -> None:
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        def show(data: bytes) -> None:
            try:
                parsed = as_dict(parse_standard_heart_rate_measurement(data))
            except ValueError as exc:
                parsed = {"raw_hex": to_hex(data), "error": str(exc)}
            print_json(parsed)

        await client.notify(STANDARD_HR_MEASUREMENT_UUID, show, seconds=args.seconds)


async def hr_oura_command(args: argparse.Namespace) -> None:
    capability_id = OURA_FEATURE_CAPABILITIES[args.source]
    request = build_oura_latest_heart_rate_request(capability_id)
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        response = await client.wait_for_oura_response(
            request,
            timeout=args.response_timeout,
            write_response=True,
        )
    parsed = as_dict(parse_oura_latest_heart_rate_response(response, capability_id))
    parsed["sent_hex"] = to_hex(request)
    print_json(parsed)


async def read_all_command(args: argparse.Namespace) -> None:
    result: dict[str, object] = {}
    async with BluetoothClient(args.address, timeout=args.timeout) as client:
        services = await client.list_services()
        result["services"] = services

        standard_rows = []
        if args.standard_seconds > 0:
            def collect_standard(data: bytes) -> None:
                try:
                    standard_rows.append(as_dict(parse_standard_heart_rate_measurement(data)))
                except ValueError as exc:
                    standard_rows.append({"raw_hex": to_hex(data), "error": str(exc)})

            try:
                await client.notify(
                    STANDARD_HR_MEASUREMENT_UUID,
                    collect_standard,
                    seconds=args.standard_seconds,
                )
            except Exception as exc:
                standard_rows.append({"error": str(exc)})
        result["standard_heart_rate"] = standard_rows

        oura_rows = []
        for source, capability_id in OURA_FEATURE_CAPABILITIES.items():
            request = build_oura_latest_heart_rate_request(capability_id)
            try:
                response = await client.wait_for_oura_response(
                    request,
                    timeout=args.response_timeout,
                    write_response=True,
                )
                parsed = as_dict(parse_oura_latest_heart_rate_response(response, capability_id))
                parsed["sent_hex"] = to_hex(request)
                oura_rows.append(parsed)
            except Exception as exc:
                oura_rows.append({"source": source, "sent_hex": to_hex(request), "error": str(exc)})
        result["oura_heart_rate"] = oura_rows

    print_json(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oura-full-read")
    parser.add_argument("--version", action="version", version="oura-full-read 0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan Bluetooth devices")
    scan_parser.add_argument("--timeout", type=float, default=10.0)
    scan_parser.add_argument("--oura-only", action="store_true")
    scan_parser.add_argument("--heart-rate-only", action="store_true")
    scan_parser.set_defaults(func=scan_command)

    services = subparsers.add_parser("services", help="list services and characteristics")
    services.add_argument("address")
    services.add_argument("--timeout", type=float, default=20.0)
    services.set_defaults(func=services_command)

    read = subparsers.add_parser("read", help="read any characteristic")
    read.add_argument("address")
    read.add_argument("characteristic")
    read.add_argument("--timeout", type=float, default=20.0)
    read.set_defaults(func=read_command)

    write = subparsers.add_parser("write", help="write any characteristic")
    write.add_argument("address")
    write.add_argument("characteristic")
    write.add_argument("hex")
    write.add_argument("--with-response", action="store_true")
    write.add_argument("--timeout", type=float, default=20.0)
    write.set_defaults(func=write_command)

    notify = subparsers.add_parser("notify", help="subscribe to any notifying characteristic")
    notify.add_argument("address")
    notify.add_argument("characteristic")
    notify.add_argument("--seconds", type=float, default=30.0)
    notify.add_argument("--timeout", type=float, default=20.0)
    notify.set_defaults(func=notify_command)

    hr_standard = subparsers.add_parser(
        "hr-standard",
        help="read standard BLE Heart Rate Measurement notifications",
    )
    hr_standard.add_argument("address")
    hr_standard.add_argument("--seconds", type=float, default=30.0)
    hr_standard.add_argument("--timeout", type=float, default=20.0)
    hr_standard.set_defaults(func=hr_standard_command)

    hr_oura = subparsers.add_parser("hr-oura", help="read Oura latest HR feature values")
    hr_oura.add_argument("address")
    hr_oura.add_argument(
        "--source",
        choices=sorted(OURA_FEATURE_CAPABILITIES),
        default="daytime-hr",
    )
    hr_oura.add_argument("--timeout", type=float, default=20.0)
    hr_oura.add_argument("--response-timeout", type=float, default=5.0)
    hr_oura.set_defaults(func=hr_oura_command)

    read_all = subparsers.add_parser(
        "read-all",
        help="list Bluetooth services and attempt standard and Oura HR reads",
    )
    read_all.add_argument("address")
    read_all.add_argument("--standard-seconds", type=float, default=10.0)
    read_all.add_argument("--timeout", type=float, default=20.0)
    read_all.add_argument("--response-timeout", type=float, default=5.0)
    read_all.set_defaults(func=read_all_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
