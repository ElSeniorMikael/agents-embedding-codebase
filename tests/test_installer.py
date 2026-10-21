from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallerTests(unittest.TestCase):
    def test_installer_copies_only_runtime_files(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            install_dir = project_root / ".agents"
            env = {**os.environ, "AGENT_INDEX_INSTALL_DIR": str(install_dir)}
            subprocess.run([str(repo_root / "install.sh")], cwd=project_root, env=env, check=True, capture_output=True, text=True)

            self.assertTrue((install_dir / "project_index.py").is_file())
            self.assertTrue((install_dir / "bin" / "agent-index").is_file())
            self.assertTrue((install_dir / "README.md").is_file())
            self.assertTrue((install_dir / "src" / "cli.py").is_file())
            self.assertFalse((install_dir / "tests").exists())
            self.assertFalse((install_dir / "docs").exists())
            self.assertFalse((install_dir / ".github").exists())


if __name__ == "__main__":
    unittest.main()
