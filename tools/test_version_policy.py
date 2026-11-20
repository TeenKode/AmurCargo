"""Regression tests for the mandatory project version and HTML badge contract."""
import unittest

from check_version import extract_badge, parse_version


class VersionTests(unittest.TestCase):
    def test_patch_increment(self):
        self.assertLess(parse_version("1.0.0"), parse_version("1.0.1"))
        self.assertLess(parse_version("1.9.9"), parse_version("1.10.0"))

    def test_bad_semver_rejected(self):
        for invalid in ("1.0", "1.0.1-beta", "01.0.1", "v1.0.1", ""):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_version(invalid)

    def test_badge(self):
        good = '<span class="version-badge" data-project-version="1.0.1">v1.0.1</span>'
        self.assertEqual(extract_badge(good), "1.0.1")
        with self.assertRaises(ValueError):
            extract_badge('<span data-project-version="1.0.0">v1.0.1</span>')
        with self.assertRaises(ValueError):
            extract_badge(good + good)


if __name__ == "__main__":
    unittest.main()
