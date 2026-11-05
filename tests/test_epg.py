import calendar
import datetime
import os
import tempfile
import unittest

from core.epg import (
    ora_xmltv, unisci_programmi, unisci_guide, piu_nuova,
    nome_epg, nome_piatto, guide_da_aggiornare,
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
        self.assertEqual(nome_piatto("Rai 4K HD"), "rai4k")
        self.assertTrue(piu_nuova("1.10", "1.9"))
        self.assertFalse(piu_nuova("1.8", "1.9"))

    def test_remote_guide_refreshes_after_six_hours(self):
        with tempfile.TemporaryDirectory() as root:
            with unittest.mock.patch("core.epg.CACHE_EPG", root):
                source = "https://example.test/guide.xml"
                import hashlib
                cache = os.path.join(root, hashlib.md5(source.encode()).hexdigest())
                with open(cache, "wb") as stream:
                    stream.write(b"guide")
                os.utime(cache, (1000, 1000))
                self.assertTrue(guide_da_aggiornare([source], 900, 1000, ora=22600))
                self.assertFalse(guide_da_aggiornare([source], 900, 1000, ora=19000))

    def test_local_guide_refreshes_when_file_changes(self):
        with tempfile.TemporaryDirectory() as root:
            source = os.path.join(root, "guide.xml")
            with open(source, "wb") as stream:
                stream.write(b"guide")
            os.utime(source, (2000, 2000))
            self.assertTrue(guide_da_aggiornare([source], 1000, 1000, ora=5000))
            self.assertFalse(guide_da_aggiornare([source], 3000, 1000, ora=5000))

    def test_epg_refresh_waits_one_hour_after_attempt(self):
        self.assertFalse(guide_da_aggiornare(["https://example.test/guide.xml"], 0, 5000, ora=8599))

if __name__ == "__main__":
    unittest.main()
