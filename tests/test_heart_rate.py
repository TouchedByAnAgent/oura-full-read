import unittest

from oura_full_read.constants import OURA_FEATURE_CAPABILITIES
from oura_full_read.heart_rate import (
    build_oura_latest_heart_rate_request,
    parse_oura_latest_heart_rate_response,
    parse_standard_heart_rate_measurement,
)
from oura_full_read.util import parse_hex, to_hex


class FullReaderHeartRateTests(unittest.TestCase):
    def test_standard_heart_rate_uint8(self):
        parsed = parse_standard_heart_rate_measurement(bytes.fromhex("0658"))
        self.assertEqual(parsed.heart_rate_bpm, 88)
        self.assertTrue(parsed.sensor_contact_supported)
        self.assertTrue(parsed.sensor_contact_detected)
        self.assertIsNone(parsed.energy_expended)
        self.assertEqual(parsed.rr_intervals_seconds, ())

    def test_standard_heart_rate_uint16_energy_and_rr(self):
        parsed = parse_standard_heart_rate_measurement(bytes.fromhex("19f40134127803"))
        self.assertEqual(parsed.heart_rate_bpm, 500)
        self.assertEqual(parsed.energy_expended, 0x1234)
        self.assertEqual(parsed.rr_intervals_seconds, (0.8671875,))

    def test_oura_latest_daytime_hr(self):
        capability = OURA_FEATURE_CAPABILITIES["daytime-hr"]
        self.assertEqual(build_oura_latest_heart_rate_request(capability), bytes.fromhex("2f022402"))
        response = bytes.fromhex("2f1025020001020a00e803040302017b0009")
        parsed = parse_oura_latest_heart_rate_response(response, capability)
        self.assertEqual(parsed.source, "daytime-hr")
        self.assertEqual(parsed.values["rr_corrected_ibi_ms"], 1000)
        self.assertEqual(parsed.values["heart_rate_bpm"], 60.0)

    def test_hex_helpers(self):
        self.assertEqual(parse_hex("2f:02:24:02"), bytes.fromhex("2f022402"))
        self.assertEqual(to_hex(bytes.fromhex("2f022402")), "2f022402")


if __name__ == "__main__":
    unittest.main()
