import unittest
from unittest.mock import patch

from core import metadata


class TMDBMetadataTests(unittest.TestCase):
    def test_genres_are_cached_per_language_and_merged_from_movie_and_tv(self):
        responses = [
            {"genres": [{"id": 28, "name": "Action"}]},
            {"genres": [{"id": 10759, "name": "Action & Adventure"}]}
        ]
        with patch.object(metadata, "_tmdb", side_effect=responses) as request:
            cache = {}
            result = metadata.generi_tmdb("token", "en-US", cache)
            self.assertEqual(result, {"28": "Action", "10759": "Action & Adventure"})
            self.assertIs(metadata.generi_tmdb("token", "en-US", cache), result)
            self.assertEqual(request.call_count, 2)

    def test_movie_metadata_prefers_result_with_poster(self):
        movie = {"results": [
            {"title": "First", "release_date": "2001-01-01", "genre_ids": [18],
             "vote_average": 6.1, "vote_count": 10},
            {"title": "Second", "release_date": "2002-02-02", "genre_ids": [28],
             "vote_average": 7.5, "vote_count": 20, "poster_path": "/second.jpg"}
        ]}
        with patch.object(metadata, "_tmdb", side_effect=[movie]):
            result = metadata.info_tmdb("token", "Film", "2002", "en-US")
        self.assertEqual(result, {
            "titolo": "Second", "anno": "2002", "generi": ["28"],
            "voto": 7.5, "voti": 20, "poster": metadata.TMDB_IMG + "/second.jpg"
        })

    def test_returns_none_when_movie_and_tv_searches_are_empty(self):
        with patch.object(metadata, "_tmdb", side_effect=[{"results": []}, {"results": []}]):
            self.assertIsNone(metadata.info_tmdb("token", "Missing", None, "en-US"))


if __name__ == "__main__":
    unittest.main()
