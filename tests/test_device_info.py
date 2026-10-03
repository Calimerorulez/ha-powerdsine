"""Metadata parsing tests without a Home Assistant runtime dependency."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'device_info', Path(__file__).parents[1] / 'custom_components/powerdsine/device_info.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parse = module.parse_system_description


class DeviceInformationTests(unittest.TestCase):
    def test_labelled_versions_preserve_serial_zeroes(self):
        self.assertEqual(parse(
            'Midspan. Unit S/N=000123. App Ver=5.13.09.14, Nov 2 2016, '
            '14:42:44. BOOT Ver=1.07, Jul 8 2009, 15:34:57 '
        ), {'serial_number': '000123', 'software_version': '5.13.09.14', 'boot_version': '1.07'})

    def test_missing_unknown_and_malformed_descriptions(self):
        for value in (None, '', 123, 'Midspan 5.13.09.14 Nov 2 2016', 'App Ver=5.13.invalid'):
            with self.subTest(value=value):
                self.assertEqual(parse(value), {})

    def test_partial_description_and_case(self):
        self.assertEqual(parse('boot ver = 1.07'), {'boot_version': '1.07'})
        self.assertEqual(parse('Unit S/N=AB-001.'), {'serial_number': 'AB-001'})


if __name__ == '__main__':
    unittest.main()
