import json
import unittest

from core.stream import chiavi_clearkey, chiave_clearkey, manifest_pulito


class StreamLogicTests(unittest.TestCase):
    def test_single_clear_key(self):
        key = "0123456789abcdef0123456789abcdef"
        self.assertEqual(chiavi_clearkey(key), [("", key)])
        self.assertEqual(chiave_clearkey(key), key)

    def test_key_id_and_key_pair(self):
        kid = "11111111111111111111111111111111"
        key = "22222222222222222222222222222222"
        self.assertEqual(chiavi_clearkey(kid + ":" + key), [(kid, key)])

    def test_json_and_url_encoded_clear_keys(self):
        kid = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        key = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        value = json.dumps({kid: key})
        self.assertEqual(chiavi_clearkey(value), [(kid, key)])
        self.assertEqual(chiavi_clearkey("%7B%22" + kid + "%22%3A%22" + key + "%22%7D"), [(kid, key)])

    def test_zero_keys_are_rejected(self):
        self.assertEqual(chiavi_clearkey("0" * 32), [])
        self.assertIsNone(chiave_clearkey("not-a-key"))

    def test_dash_manifest_removes_subtitles_and_adds_base_url(self):
        manifest = (
            "<MPD><Period><AdaptationSet mimeType=\"video/mp4\"></AdaptationSet>"
            "<AdaptationSet mimeType=\"text/vtt\"><Representation/></AdaptationSet>"
            "</Period></MPD>"
        )
        result = manifest_pulito(manifest, "https://example.org/live/manifest.mpd")
        self.assertIn("<BaseURL>https://example.org/live/</BaseURL>", result)
        self.assertIn('mimeType="video/mp4"', result)
        self.assertNotIn('mimeType="text/vtt"', result)


if __name__ == "__main__":
    unittest.main()
