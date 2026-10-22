from __future__ import annotations

import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallerTests(unittest.TestCase):
    def test_installer_copies_only_runtime_files(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            install_dir = project_root / ".agents" / "embedding-codebase"
            env = {key: value for key, value in os.environ.items() if not key.startswith("AGENT_INDEX_")}
            subprocess.run([str(repo_root / "install.sh")], cwd=project_root, env=env, check=True, capture_output=True, text=True)

            self.assertTrue((install_dir / "project_index.py").is_file())
            self.assertTrue((install_dir / "bin" / "agent-index").is_file())
            self.assertTrue((install_dir / "README.md").is_file())
            self.assertTrue((install_dir / "src" / "cli.py").is_file())
            self.assertFalse((install_dir / "tests").exists())
            self.assertFalse((install_dir / "docs").exists())
            self.assertFalse((install_dir / ".github").exists())

    def test_installed_commands_index_project_for_supported_layouts(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        for layout in (".agents/embedding-codebase", ".agents", ".codex", ".agents/custom-runtime"):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as tmp:
                project_root = Path(tmp)
                install_dir = project_root / layout
                env = {key: value for key, value in os.environ.items() if not key.startswith("AGENT_INDEX_")}
                env.update({
                    "AGENT_INDEX_INSTALL_DIR": str(install_dir),
                    "AGENT_INDEX_INSTALL_GLOBAL": "1",
                    "AGENT_INDEX_GLOBAL_BIN_DIR": str(project_root / "global-bin"),
                })
                if layout == ".agents/custom-runtime":
                    env["AGENT_INDEX_DIR_NAMES"] = layout
                subprocess.run([str(repo_root / "install.sh")], cwd=project_root, env=env, check=True, capture_output=True, text=True)
                source_dir = project_root / "app" / "nested"
                source_dir.mkdir(parents=True)
                (source_dir / "example.py").write_text("def searchable_example():\n    return 42\n")
                (project_root / "excluded.txt").write_text("excluded content")
                (install_dir / "index.config.json").write_text(json.dumps({"exclude": ["excluded.txt"]}))

                for command, cwd in ((install_dir / "bin" / "agent-index", project_root),
                                     (project_root / "global-bin" / "agent-index", source_dir)):
                    subprocess.run([str(command), "update"], cwd=cwd, env=env, check=True, capture_output=True, text=True)
                    index = json.loads((install_dir / "index" / "index.json").read_text())
                    self.assertEqual(set(index["files"]), {"app/nested/example.py"})
                    result = subprocess.run([str(command), "search", "searchable_example"], cwd=cwd, env=env, check=True, capture_output=True, text=True)
                    self.assertIn("app/nested/example.py", result.stdout)

                override_root = project_root / "override"
                override_root.mkdir()
                (override_root / "other.py").write_text("value = 1\n")
                env["AGENT_INDEX_ROOT"] = str(override_root)
                subprocess.run([str(install_dir / "bin" / "agent-index"), "update"], cwd=project_root, env=env, check=True, capture_output=True, text=True)
                index = json.loads((install_dir / "index" / "index.json").read_text())
                self.assertEqual(set(index["files"]), {"other.py"})


if __name__ == "__main__":
    unittest.main()
