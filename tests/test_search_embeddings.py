from __future__ import annotations

import unittest
from unittest import mock

from src import embedding_cache
from src.embedding_cache import embedding_cache_key, normalized_query_text, prune_query_cache
from src.hybrid_search import score_hybrid_chunks
from src.lexical_search import score_chunks
from src.search_utils import normalize_scores, search_symbols, snippet, symbol_list_match_score, symbols_by_path
from src.vectors import cosine_similarity, dot, norm, normalize_vector


class VectorTests(unittest.TestCase):
    def test_vector_math(self) -> None:
        self.assertEqual(dot([1, 2], [3, 4]), 11)
        self.assertEqual(norm([3, 4]), 5)
        self.assertEqual(normalize_vector([0, 0]), [0.0, 0.0])
        self.assertAlmostEqual(cosine_similarity([1, 0], [1, 0]), 1.0)


class SearchTests(unittest.TestCase):
    def test_score_chunks_ranks_token_matches(self) -> None:
        index = {
            "chunk_count": 2,
            "doc_freq": {"alpha": 1},
            "chunks": [
                {"id": "a", "path": "src/alpha.py", "tokens": {"alpha": 2}, "text": "alpha"},
                {"id": "b", "path": "src/beta.py", "tokens": {"beta": 1}, "text": "beta"},
            ],
        }
        matches = score_chunks(index, "alpha", 5)
        self.assertEqual(matches[0][1]["id"], "a")

    def test_normalize_scores_handles_equal_scores(self) -> None:
        self.assertEqual(normalize_scores([(2.0, {"id": "a"}), (2.0, {"id": "b"})]), {"a": 1.0, "b": 1.0})

    def test_search_symbols_and_snippet(self) -> None:
        index = {"symbols": [{"path": "a.py", "line": 2, "kind": "function", "name": "find_user"}]}
        self.assertEqual(search_symbols(index, "user", 5)[0]["name"], "find_user")
        self.assertIn("target", snippet("hello target world", "target"))

    def test_symbols_by_path_and_scoring(self) -> None:
        index = {"symbols": [{"path": "a.py", "line": 3, "name": "SearchThing"}]}
        grouped = symbols_by_path(index)
        score = symbol_list_match_score(grouped["a.py"], {"path": "a.py", "start": 1, "end": 5}, ["search"])
        self.assertEqual(score, 0.8)

    def test_hybrid_search_fuses_lexical_and_semantic_scores(self) -> None:
        index = {
            "chunk_count": 1,
            "doc_freq": {"alpha": 1},
            "symbols": [{"path": "alpha.py", "line": 1, "name": "alpha_symbol"}],
            "chunks": [{"id": "a", "path": "alpha.py", "start": 1, "end": 2, "tokens": {"alpha": 1}, "text": "alpha"}],
        }
        with mock.patch("src.hybrid_search.score_semantic_chunks", return_value=[(0.9, index["chunks"][0])]):
            matches = score_hybrid_chunks(index, "alpha", 3, 0.5, 0.5)
        self.assertEqual(matches[0][1]["id"], "a")
        self.assertGreater(matches[0][0], 0)


class EmbeddingCacheTests(unittest.TestCase):
    def test_normalized_query_text_and_key_are_stable(self) -> None:
        self.assertEqual(normalized_query_text("  Hello   WORLD "), "hello world")
        self.assertEqual(
            embedding_cache_key("openai", "model", None, "Hello WORLD"),
            embedding_cache_key("openai", "model", None, "hello   world"),
        )

    def test_prune_query_cache_keeps_most_recent_entries(self) -> None:
        cache = {"queries": {str(i): {"created_at": i} for i in range(505)}}
        prune_query_cache(cache)
        self.assertEqual(len(cache["queries"]), 500)
        self.assertNotIn("0", cache["queries"])
        self.assertIn("504", cache["queries"])

    def test_query_embedding_uses_cached_normalized_vector(self) -> None:
        cached = [1.0, 0.0]
        cache = {
            "queries": {
                embedding_cache_key("openai", "model", None, "hello"): {
                    "provider": "openai",
                    "model": "model",
                    "dimensions": None,
                    "query": "hello",
                    "normalized_embedding": cached,
                }
            }
        }
        with (
            mock.patch.object(embedding_cache, "load_query_embeddings", return_value=cache),
            mock.patch.object(embedding_cache, "write_query_embeddings") as write,
            mock.patch.object(embedding_cache, "embedding_request") as request,
        ):
            result = embedding_cache.query_embedding("hello", "model", None, "openai")
        self.assertEqual(result, cached)
        request.assert_not_called()
        write.assert_called_once()


if __name__ == "__main__":
    unittest.main()
