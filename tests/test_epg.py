import calendar
import datetime
import os
import tempfile
import unittest

from core.epg import (
    ora_xmltv, unisci_programmi, unisci_guide, piu_nuova,
    nome_epg, nome_piatto,
)


class EpgLogicTests(unittest.TestCase):
    def test_xmltv_timezone_conversion(self):
        expected = calendar.timegm((2026, 11, 5, 18, 0, 0, 0, 0, 0))
        self.assertEqual(ora_xmltv("20261105200000 +0200"), expected)
        self.assertIsNone(ora_xmltv("not-a-date"))

    def test_merge_programs_keeps_base_and_skips_overlaps(self):
        base = [(100, 200, "Base")]
        other = [(50, 110, "Overlap"), (200, 250, "Adjacent"), (300, 400, "Later")]
        self.assertEqual(unisci_programmi(base, other), [
            (50, 110, "Overlap"),
            (100, 200, "Base"),
            (200, 250, "Adjacent"),
            (300, 400, "Later"),
        ])

    def test_guide_merge_unifies_shared_channel_ids(self):
        names, programs = unisci_guide([
            ({"news": "id-a"}, {"id-a": [(10, 20, "A")]}),
            ({"news": "id-b"}, {"id-b": [(20, 30, "B")]}),
        ])
        self.assertEqual(names["news"], "id-a")
        self.assertEqual(programs["id-a"], [(10, 20, "A"), (20, 30, "B")])
        self.assertEqual(programs["id-b"], programs["id-a"])

    def test_names_and_version_comparison(self):
        self.assertEqual(nome_epg("https://example.org/guide.xml.gz"), "guide.xml")
        self.assertEqual(nome_epg("https://www.example.org/"), "example.org")
        self.assertEqual(nome_piatto("Rai 4K HD"), "rai")
        self.assertTrue(piu_nuova("1.10", "1.9"))
        self.assertFalse(piu_nuova("1.8", "1.9"))


if __name__ == "__main__":
    unittest.main()
