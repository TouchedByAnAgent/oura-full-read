# Full Reader Source Tree

`full_reader/src/oura_full_read` is a separate Python source tree for direct Bluetooth and heart-rate reading.

It is intentionally separate from `standalone/src/oura_ble_control`. The earlier package exposes a wider set of decoded Oura operations. This package focuses on:

- Bluetooth scanning.
- Bluetooth service and characteristic inspection.
- Generic characteristic read/write/notify.
- Standard BLE Heart Rate Service reading.
- Oura custom latest heart-rate feature reading.
- A combined `read-all` workflow for Bluetooth inventory plus heart-rate attempts.

## Install

```bash
cd full_reader
python -m pip install -e .
```

## Commands

Scan:

```bash
oura-full-read scan --timeout 10
oura-full-read scan --oura-only
oura-full-read scan --heart-rate-only
```

Bluetooth services:

```bash
oura-full-read services AA:BB:CC:DD:EE:FF
```

Generic characteristic operations:

```bash
oura-full-read read AA:BB:CC:DD:EE:FF 00002a37-0000-1000-8000-00805f9b34fb
oura-full-read write AA:BB:CC:DD:EE:FF 98ed0002-a541-11e4-b6a0-0002a5d5c51b 0c00 --with-response
oura-full-read notify AA:BB:CC:DD:EE:FF 98ed0003-a541-11e4-b6a0-0002a5d5c51b --seconds 30
```

Standard BLE heart-rate monitor:

```bash
oura-full-read hr-standard AA:BB:CC:DD:EE:FF --seconds 30
```

Oura custom heart-rate latest values:

```bash
oura-full-read hr-oura AA:BB:CC:DD:EE:FF --source daytime-hr
oura-full-read hr-oura AA:BB:CC:DD:EE:FF --source exercise-hr
oura-full-read hr-oura AA:BB:CC:DD:EE:FF --source spo2
```

Combined read:

```bash
oura-full-read read-all AA:BB:CC:DD:EE:FF --standard-seconds 20
```

## Heart-Rate Paths

Standard BLE HR uses:

- Service: `0000180d-0000-1000-8000-00805f9b34fb`
- Measurement characteristic: `00002a37-0000-1000-8000-00805f9b34fb`

Oura custom HR uses:

- Service: `98ed0001-a541-11e4-b6a0-0002a5d5c51b`
- Write characteristic: `98ed0002-a541-11e4-b6a0-0002a5d5c51b`
- Read/notify characteristic: `98ed0003-a541-11e4-b6a0-0002a5d5c51b`
- Latest values request: `2f0224{capability}`

Supported Oura HR sources:

| Source | Capability |
| --- | ---: |
| `daytime-hr` | `2` |
| `exercise-hr` | `3` |
| `spo2` | `4` |

The decoded app uses the standard Heart Rate Service UUID to identify third-party HR monitors. Oura ring HR itself is read through the custom feature protocol above.
