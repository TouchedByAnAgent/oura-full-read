# Oura Full Read

This is a separate `src` package for direct Bluetooth inspection and heart-rate reading.

It supports two heart-rate paths:

- Standard BLE Heart Rate Service devices using service `0000180d-0000-1000-8000-00805f9b34fb` and characteristic `00002a37-0000-1000-8000-00805f9b34fb`.
- Oura's custom BLE service using the decoded latest-values request for `CAP_DAYTIME_HR`, `CAP_EXERCISE_HR`, and SpO2-linked HR values.

The Oura ring does not expose its own heart rate through the standard BLE Heart Rate Service in the decoded app. The standard reader is included so this package can fully read normal Bluetooth HR monitors as well as Oura's custom latest HR path.

## Install

```bash
cd full_reader
python -m pip install -e .
```

## Bluetooth Commands

Scan nearby devices:

```bash
oura-full-read scan --timeout 10
oura-full-read scan --oura-only
oura-full-read scan --heart-rate-only
```

List services and characteristics:

```bash
oura-full-read services AA:BB:CC:DD:EE:FF
```

Read, write, or notify any characteristic:

```bash
oura-full-read read AA:BB:CC:DD:EE:FF 00002a37-0000-1000-8000-00805f9b34fb
oura-full-read write AA:BB:CC:DD:EE:FF 98ed0002-a541-11e4-b6a0-0002a5d5c51b 0c00 --with-response
oura-full-read notify AA:BB:CC:DD:EE:FF 98ed0003-a541-11e4-b6a0-0002a5d5c51b --seconds 30
```

## Heart-Rate Commands

Read a standard BLE heart-rate monitor continuously:

```bash
oura-full-read hr-standard AA:BB:CC:DD:EE:FF --seconds 30
```

Read Oura's latest custom heart-rate feature values:

```bash
oura-full-read hr-oura AA:BB:CC:DD:EE:FF --source daytime-hr
oura-full-read hr-oura AA:BB:CC:DD:EE:FF --source exercise-hr
oura-full-read hr-oura AA:BB:CC:DD:EE:FF --source spo2
```

Run the combined reader, which lists Bluetooth services and then attempts both standard and Oura HR paths:

```bash
oura-full-read read-all AA:BB:CC:DD:EE:FF --standard-seconds 20
```

## Limits

Oura feature reads may require bonding, encryption, and a ring state that accepts the request. This package does not bypass authentication or account-backed authorization.
