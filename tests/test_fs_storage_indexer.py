from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import fs, indexer, storage
from src.embeddings import chunk_embedding_text, text_hash
from src.fs import FileEntry


class FilesystemTests(unittest.TestCase):
    def test_matches_any_uses_shell_patterns(self) -> None:
        self.assertTrue(fs.matches_any("node_modules/pkg/index.js", ("node_modules/**",)))
        self.assertFalse(fs.matches_any("src/index.py", ("node_modules/**",)))

    def test_read_text_rejects_binary_and_decodes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / "a.txt"
            text_path.write_text("hello", encoding="utf-8")
            binary_path = root / "b.txt"
            binary_path.write_bytes(b"\0binary")
            self.assertEqual(fs.read_text(text_path), "hello")
            self.assertIsNone(fs.read_text(binary_path))

    def test_read_file_entry_returns_metadata_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = Path(tmp) / "a.py"
            path.write_text("print('hi')\n", encoding="utf-8")
            with mock.patch.object(fs, "rel", lambda value: Path(value).relative_to(root).as_posix()):
                entry, text = fs.read_file_entry(path)  # type: ignore[misc]
            self.assertEqual(entry.path, "a.py")
            self.assertEqual(text, "print('hi')\n")


class StorageTests(unittest.TestCase):
    def test_empty_index_has_expected_shape(self) -> None:
        data = storage.empty_index()
        self.assertEqual(data["files"], {})
        self.assertEqual(data["chunks"], [])
        self.assertEqual(data["chunk_count"], 0)

    def test_load_index_returns_empty_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index_dir = Path(tmp) / "index"
            index_file = index_dir / "index.json"
            embeddings_file = index_dir / "embeddings.json"
            query_file = index_dir / "query_embeddings.json"
            index_dir.mkdir()
            index_file.write_text("{bad", encoding="utf-8")
            with (
                mock.patch.object(storage, "INDEX_DIR", index_dir),
                mock.patch.object(storage, "INDEX_FILE", index_file),
                mock.patch.object(storage, "EMBEDDINGS_FILE", embeddings_file),
                mock.patch.object(storage, "QUERY_EMBEDDINGS_FILE", query_file),
                mock.patch.object(storage, "ROOT", Path(tmp)),
            ):
                self.assertEqual(storage.load_index()["files"], {})

    def test_rebuild_vectors_counts_document_frequency(self) -> None:
        data = {"chunks": [{"tokens": {"alpha": 2, "beta": 1}}, {"tokens": {"alpha": 1}}]}
        storage.rebuild_vectors(data)
        self.assertEqual(data["doc_freq"], {"alpha": 2, "beta": 1})
        self.assertEqual(data["chunk_count"], 2)


class IndexerTests(unittest.TestCase):
    def test_unchanged_entry_reuses_old_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.py"
            path.write_text("print('hi')\n", encoding="utf-8")
            stat = path.stat()
            old = {"path": "a.py", "sha256": "abc", "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            with mock.patch.object(indexer, "rel", lambda value: Path(value).name):
                entry = indexer.unchanged_entry(path, old)
            self.assertEqual(entry, FileEntry(path="a.py", sha256="abc", size=stat.st_size, mtime_ns=stat.st_mtime_ns))

    def test_embedding_freshness_counts_missing_stale_and_extra(self) -> None:
        current = {"id": "current", "path": "a.py", "start": 1, "end": 1, "text": "hello"}
        stale = {"id": "stale", "path": "b.py", "start": 1, "end": 1, "text": "changed"}
        stale_hash = text_hash(chunk_embedding_text({**stale, "text": "old"}))
        result = indexer.embedding_freshness(
            {"chunks": [current, stale]},
            {"chunks": {"stale": {"text_sha256": stale_hash}, "extra": {"text_sha256": "x"}}},
        )
        self.assertEqual(result, {"missing": 1, "stale": 1, "extra": 1, "total": 2})

    def test_update_index_writes_index_for_temp_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent_dir = root / ".agents"
            index_dir = agent_dir / "index"
            agent_dir.mkdir()
            (root / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
            index_file = index_dir / "index.json"
            with (
                mock.patch.object(fs, "ROOT", root),
                mock.patch.object(fs, "AGENT_DIR", agent_dir),
                mock.patch.object(fs, "rel", lambda value: Path(value).relative_to(root).as_posix()),
                mock.patch.object(indexer, "INDEX_FILE", index_file),
                mock.patch.object(indexer, "rel", lambda value: Path(value).relative_to(root).as_posix()),
                mock.patch.object(storage, "ROOT", root),
                mock.patch.object(storage, "INDEX_DIR", index_dir),
                mock.patch.object(storage, "INDEX_FILE", index_file),
                mock.patch.object(storage, "EMBEDDINGS_FILE", index_dir / "embeddings.json"),
                mock.patch.object(storage, "QUERY_EMBEDDINGS_FILE", index_dir / "query_embeddings.json"),
            ):
                stats = indexer.update_index(full=True)
            self.assertEqual(stats["files"], 1)
            self.assertGreater(stats["chunks"], 0)
            self.assertTrue(json.loads(index_file.read_text(encoding="utf-8"))["files"]["app.py"])


if __name__ == "__main__":
    unittest.main()
