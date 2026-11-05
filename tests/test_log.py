import logging
import unittest

from core.log import _XVBFiltroSicurezza


class SecureLoggingTests(unittest.TestCase):
    def test_credentials_in_parameters_are_redacted(self):
        record = logging.LogRecord("xvb", logging.INFO, "", 0,
                                   "token=secret123&name=channel", (), None)
        _XVBFiltroSicurezza().filter(record)
        self.assertEqual(record.getMessage(), "token=[REDACTED]&name=channel")

    def test_credentials_in_url_are_redacted(self):
        record = logging.LogRecord("xvb", logging.INFO, "", 0,
                                   "https://alice:password@example.org/live", (), None)
        _XVBFiltroSicurezza().filter(record)
        self.assertEqual(record.getMessage(), "https://[REDACTED]@example.org/live")


if __name__ == "__main__":
    unittest.main()
