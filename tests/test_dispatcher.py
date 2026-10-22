from __future__ import annotations

import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock


class DispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dispatcher = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bin/agent-index"))

    def test_windows_path_list_preserves_drive_letters(self) -> None:
        with mock.patch.dict(os.environ, {"AGENT_INDEX_DIR_NAMES": r"C:\tools\index;.agents/embedding-codebase"}), mock.patch("os.pathsep", ";"):
            self.assertEqual(self.dispatcher["candidate_names"](), (r"C:\tools\index", ".agents/embedding-codebase"))

    def test_nested_project_discovery_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project with spaces ") as tmp:
            root = Path(tmp)
            runtime = root / ".agents/embedding-codebase"
            (runtime / "src").mkdir(parents=True)
            (runtime / "src/cli.py").touch()
            (runtime / "project_index.py").write_text("raise SystemExit(7)\n")
            nested = root / "app"
            nested.mkdir()
            with mock.patch.dict(os.environ, {"AGENT_INDEX_DIR_NAMES": ""}), mock.patch("pathlib.Path.cwd", return_value=nested), mock.patch("sys.argv", ["agent-index", "search", "multiple words"]):
                self.assertEqual(self.dispatcher["find_project_index"](nested), runtime / "project_index.py")
                self.assertEqual(self.dispatcher["main"](), 7)


if __name__ == "__main__":
    unittest.main()
