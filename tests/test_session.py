import unittest
from unittest.mock import patch

from core.session import Sessione
from core.playlists import NOMI_URL
from core.epg import EPG_ICONE, EPG_ICONE_NOME


class SessionTests(unittest.TestCase):
    def test_loads_named_url_playlists_and_nested_categories(self):
        config = {
            "liste": ["/custom/manual.m3u", "/missing.m3u"],
            "liste_url": {"https://example.test/live.m3u": "Example Live"},
            "nomi_liste": {"/custom/manual.m3u": "Manual"},
            "epg": [],
        }
        canali = [
            ("Channel A", "https://stream.test/a", "a"),
            ("Channel B", "https://stream.test/b", "b"),
        ]
        with patch("core.session.leggi_config", return_value=config), \
             patch("core.session.liste_in_cartella", return_value=["/lists/root.m3u"]), \
             patch("core.session.categorie", return_value=[("Sports", ["/lists/sports.m3u"])]), \
             patch("core.session.os.path.isfile", side_effect=lambda p: p != "/missing.m3u"), \
             patch("core.session.leggi_lista", return_value=canali), \
             patch("core.session.categorie_m3u", return_value={"https://stream.test/a": "News"}), \
             patch("core.session.leggi_preferiti_cat", return_value=[]):
            sessione = Sessione()

        self.assertEqual(
            [v["percorso"] for v in sessione.liste],
            ["/lists/root.m3u", "/lists/sports.m3u", "/custom/manual.m3u",
             "https://example.test/live.m3u"])
        self.assertEqual(sessione.liste[1]["gruppo"], "Sports")
        self.assertEqual(sessione.liste[3]["nome"], "Example Live")
        self.assertEqual(sessione.canali[0][3], "News")
        self.assertEqual(sessione.canali[1][3], "Altri")
        self.assertEqual(NOMI_URL["https://example.test/live.m3u"], "Example Live")

    def test_loads_and_persists_name_embedded_in_gzip_guide(self):
        sessione = Sessione.__new__(Sessione)
        sessione.config = {"epg": ["https://example.test/guide.xml.gz"]}
        sessione.epg = {}
        sessione.epg_nomi = {}
        EPG_ICONE[('old', 1)] = 'old'
        EPG_ICONE_NOME[('old', 1, 'old')] = 'old'
        with patch("core.session.prendi_epg", return_value="/tmp/guide-cache"), \
             patch("core.session.nome_dentro", return_value="xmltv-original.xml"), \
             patch("core.session.leggi_epg", return_value=({"news": "news.id"}, {"news.id": [(1, 2, "News")]})), \
             patch("core.session.scrivi_config") as scrivi:
            sessione.carica_guide()
        self.assertEqual(sessione.config["epg_nomi"]["https://example.test/guide.xml.gz"], "xmltv-original.xml")
        self.assertEqual(sessione.epg_nomi, {"news": "news.id"})
        self.assertEqual(EPG_ICONE, {})
        self.assertEqual(EPG_ICONE_NOME, {})
        scrivi.assert_called_once_with(sessione.config)
    def test_empty_guide_list_clears_previous_epg_data(self):
        sessione = Sessione.__new__(Sessione)
        sessione.config = {"epg": []}
        sessione.epg_nomi = {"news": "news.id"}
        sessione.epg = {"news.id": [(1, 2, "Old programme")]}
        EPG_ICONE[('old', 1)] = 'old'
        EPG_ICONE_NOME[('old', 1, 'old')] = 'old'
        sessione.carica_guide()
        self.assertEqual(sessione.epg_nomi, {})
        self.assertEqual(sessione.epg, {})
        self.assertEqual(EPG_ICONE, {})
        self.assertEqual(EPG_ICONE_NOME, {})

if __name__ == "__main__":
    unittest.main()
