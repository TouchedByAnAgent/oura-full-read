"""Bluetooth UUIDs and decoded Oura operation constants."""

STANDARD_HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
STANDARD_HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
STANDARD_BODY_SENSOR_LOCATION_UUID = "00002a38-0000-1000-8000-00805f9b34fb"

OURA_MANUFACTURER_ID = 690
OURA_SERVICE_UUID = "98ed0001-a541-11e4-b6a0-0002a5d5c51b"
OURA_WRITE_CHARACTERISTIC_UUID = "98ed0002-a541-11e4-b6a0-0002a5d5c51b"
OURA_READ_CHARACTERISTIC_UUID = "98ed0003-a541-11e4-b6a0-0002a5d5c51b"

OURA_FEATURE_CAPABILITIES = {
    "daytime-hr": 2,
    "exercise-hr": 3,
    "spo2": 4,
}
OURA_FEATURE_NAMES = {value: key for key, value in OURA_FEATURE_CAPABILITIES.items()}

OURA_FEATURE_REQUEST_RESULTS = {
    0: "success",
    1: "not_supported",
    2: "not_available",
    3: "not_in_finger",
    4: "message_too_short",
    5: "low_battery",
}
OURA_FEATURE_STATES = {
    0: "idle",
    1: "scanning",
    2: "measuring",
    3: "postprocessing",
}
OURA_FEATURE_STATUS_BITS = {
    1: "searching",
    2: "no_reliable_ppg_signal",
    3: "cold_fingers",
    4: "too_much_movements",
    5: "identifying_signal",
}
