import unittest

from pipeline.email_validator import validate_email


class TestEmailValidator(unittest.TestCase):
    def test_format_invalid(self) -> None:
        r = validate_email("not-an-email", confidence=100)
        self.assertFalse(r.valid)
        self.assertEqual(r.reason, "format_invalid")

