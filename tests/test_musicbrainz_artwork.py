import unittest
from unittest.mock import patch

from core import metadata


class MusicBrainzArtworkTests(unittest.TestCase):
    def test_album_artwork_returns_first_release_group_and_year(self):
        response = {"release-groups": [
            {"id": "abc-123", "first-release-date": "1998-04-12"},
            {"id": "def-456", "first-release-date": "2001"}
        ]}
        with patch.object(metadata, "json_da", return_value=response):
            url, year = metadata.copertina_musicbrainz("Artist", "Album")
        self.assertEqual(url, "https://coverartarchive.org/release-group/abc-123/front-500")
        self.assertEqual(year, "1998")

    def test_track_artwork_prioritizes_official_album_and_deduplicates_urls(self):
        response = {"recordings": [
            {"releases": [
                {"status": "Bootleg", "date": "1980", "title": "Live",
                 "release-group": {"id": "live", "primary-type": "Album", "title": "Live"}},
                {"status": "Official", "date": "1990-05-01", "title": "Studio",
                 "release-group": {"id": "studio", "primary-type": "Album", "title": "Studio"}},
                {"status": "Official", "date": "1991", "title": "Studio edition",
                 "release-group": {"id": "studio", "primary-type": "Album", "title": "Studio"}}
            ]}
        ]}
        with patch.object(metadata, "json_da", return_value=response):
            urls, year, album = metadata.copertina_da_brano("Artist", "Track")
        self.assertEqual(urls, [
            "https://coverartarchive.org/release-group/studio/front-500",
            "https://coverartarchive.org/release-group/live/front-500"
        ])
        self.assertEqual(year, "1990")
        self.assertEqual(album, "Studio")

    def test_track_without_releases_returns_empty_values(self):
        with patch.object(metadata, "json_da", return_value={"recordings": []}):
            self.assertEqual(metadata.copertina_da_brano("Artist", "Track"), ([], "", ""))


if __name__ == "__main__":
    unittest.main()
