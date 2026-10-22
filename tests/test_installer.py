from __future__ import annotations

import os
import json
import sys
import shutil
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipIf(os.name == "nt", "POSIX shell installer; Windows has separate installer tests")
class InstallerTests(unittest.TestCase):
    def test_missing_or_old_python_is_installed_before_runtime(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        for initial in ("missing", "old", "install-failure", "still-old"):
            with self.subTest(initial=initial), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                tools = root / "tools"
                tools.mkdir()
                for name in ("dirname", "mkdir", "cp", "chmod", "find"):
                    (tools / name).symlink_to(shutil.which(name))
                def script(name: str, body: str) -> None:
                    path = tools / name
                    path.write_text("#!/bin/sh\n" + body)
                    path.chmod(0o755)
                script("uname", "echo Linux\n")
                script("id", "echo 0\n")
                if initial in ("old", "still-old"):
                    script("python3", "exit 1\n")
                body = 'echo "$*" >> "$INSTALL_LOG"\n'
                if initial == "install-failure":
                    body += "exit 1\n"
                elif initial != "still-old":
                    body += 'if [ "$1" = install ]; then /bin/ln -sf ' + shlex.quote(sys.executable) + ' "$TOOLS/python3"; fi\n'
                script("apt-get", body)
                env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_INDEX_")}
                env.update(PATH=str(tools), TOOLS=str(tools), INSTALL_LOG=str(root / "install.log"))
                result = subprocess.run([str(repo / "install.sh")], cwd=root, env=env, capture_output=True, text=True)
                if initial in ("install-failure", "still-old"):
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse((root / ".agents").exists())
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue((root / ".agents/embedding-codebase/project_index.py").exists())
                    self.assertEqual((root / "install.log").read_text(), "update\ninstall -y python3\n")

    def test_ollama_flag_is_opt_in_and_propagates_failure(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            fake_bin = project / "fake-bin"
            fake_bin.mkdir()
            log = project / "setup.log"
            python = fake_bin / "python3"
            python.write_text("#!/bin/sh\nif [ \"$1\" = '-m' ]; then\n  echo \"$*\" >> \"$SETUP_LOG\"\n  exit \"${SETUP_EXIT:-0}\"\nfi\nexec " + str(Path(sys.executable)) + " \"$@\"\n")
            python.chmod(0o755)
            ollama = fake_bin / "ollama"
            ollama.write_text("#!/bin/sh\nexit 0\n")
            ollama.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_INDEX_")}
            env.update(PATH=str(fake_bin) + os.pathsep + env["PATH"], SETUP_LOG=str(log))
            command = [str(repo_root / "install.sh")]
            subprocess.run(command, cwd=project, env=env, check=True, capture_output=True)
            self.assertFalse(log.exists())
            subprocess.run(command + ["--with-ollama"], cwd=project, env=env, check=True, capture_output=True)
            self.assertEqual(log.read_text().strip(), "-m src.setup_ollama")
            env["SETUP_EXIT"] = "1"
            result = subprocess.run(command + ["--with-ollama"], cwd=project, env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            result = subprocess.run(command + ["--unknown"], cwd=project, env=env, capture_output=True)
            self.assertEqual(result.returncode, 2)

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
