import unittest
from unittest.mock import patch

from core import stream


class HLSVariantTests(unittest.TestCase):
    def test_master_variants_resolve_audio_and_video_urls(self):
        body = b'''#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="Italian",URI="audio/index.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=1280x720,AUDIO="audio",CODECS="avc1.4d401f,mp4a.40.2"
video/720.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1920x1080,AUDIO="audio",CODECS="avc1.4d401f,mp4a.40.2"
video/1080.m3u8
'''
        class Response:
            def read(self, _size):
                return body
        with patch.object(stream, "urlopen", return_value=Response()):
            result = stream.varianti("https://example.org/live/master.m3u8")
        self.assertEqual(len(result), 2)
        self.assertEqual([item[0] for item in result], [1500000, 3000000])
        self.assertEqual(result[0][1], "https://example.org/live/video/720.m3u8")
        self.assertEqual(result[0][2], "https://example.org/live/audio/index.m3u8")
        self.assertEqual(result[1][3], 1080)
        self.assertIn("https://example.org/live/audio/index.m3u8", result[0][4])

    def test_non_master_and_failed_request_return_empty(self):
        class Response:
            def read(self, _size):
                return b"#EXTM3U\n#EXTINF:-1\nsegment.ts\n"
        with patch.object(stream, "urlopen", return_value=Response()):
            self.assertEqual(stream.varianti("https://example.org/live/list.m3u8"), [])
        with patch.object(stream, "urlopen", side_effect=OSError):
            self.assertEqual(stream.varianti("https://example.org/live/master.m3u8"), [])

    def test_jmp2_is_skipped(self):
        with patch.object(stream, "urlopen") as opener:
            self.assertEqual(stream.varianti("https://jmp2.uk/channel.m3u8"), [])
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
