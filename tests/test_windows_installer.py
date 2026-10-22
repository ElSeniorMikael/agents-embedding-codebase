from __future__ import annotations

import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
import zipfile


@unittest.skipUnless(os.name == "nt", "Requires Windows PowerShell and cmd.exe")
class WindowsInstallerTests(unittest.TestCase):
    def run_command(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, **kwargs)
        self.assertEqual(result.returncode, 0, f"Command failed: {command}\n{result.stdout}\n{result.stderr}")
        return result

    def test_python_bootstrap_success_and_failure(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        for exit_code in (0, 1603):
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                project = root / "project"
                project.mkdir()
                harness = root / "bootstrap.ps1"
                installer = str(repo / "install.ps1").replace("'", "''")
                harness.write_text("""
$ErrorActionPreference = 'Stop'
$global:PythonReady = $false
function python { $global:LASTEXITCODE = [int](-not $global:PythonReady) }
function py { $global:LASTEXITCODE = [int](-not $global:PythonReady) }
function Invoke-WebRequest {
    param($Uri, $OutFile, [switch]$UseBasicParsing)
    if ($Uri -notlike 'https://www.python.org/ftp/python/*') { throw 'Unexpected download' }
    Set-Content -LiteralPath $OutFile -Value 'mock installer'
}
function Start-Process {
    param($FilePath, $ArgumentList, [switch]$Wait, [switch]$PassThru)
    if ($ArgumentList -notcontains 'InstallAllUsers=0') { throw 'Must install per user' }
    if ($ArgumentList -notcontains 'PrependPath=1') { throw 'Must configure PATH' }
    $global:PythonReady = $true
    return [pscustomobject]@{ ExitCode = EXIT_CODE }
}
try {
    & 'INSTALLER'
    if (-not $global:PythonReady) { throw 'Python installation was skipped' }
} catch { Write-Error $_; exit 1 }
""".replace('EXIT_CODE', str(exit_code)).replace('INSTALLER', installer))
                env = {k: v for k, v in os.environ.items() if not k.startswith('AGENT_INDEX_')}
                result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                         '-File', str(harness)], cwd=project, env=env,
                                        capture_output=True, text=True, timeout=120)
                runtime = project / '.agents/embedding-codebase/project_index.py'
                if exit_code == 0:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertTrue(runtime.exists())
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(runtime.exists())

    def test_local_and_downloaded_installations(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        for remote in (False, True):
            with self.subTest(remote=remote), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                project = root / "dummy project"
                project.mkdir()
                env = {k: v for k, v in os.environ.items() if not k.startswith("AGENT_INDEX_")}
                env["AGENT_INDEX_GLOBAL_BIN_DIR"] = str(root / "global bin")
                installer = repo / "install.ps1"
                server = None
                if remote:
                    installer = root / "install.ps1"
                    shutil.copyfile(repo / "install.ps1", installer)
                    archive = root / "runtime.zip"
                    with zipfile.ZipFile(archive, "w") as output:
                        for path in [repo / "project_index.py", repo / "README.md",
                                     *list((repo / "bin").iterdir()), *list((repo / "src").glob("*.py"))]:
                            output.write(path, "runtime/" + path.relative_to(repo).as_posix())
                    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
                    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
                    threading.Thread(target=server.serve_forever, daemon=True).start()
                    env["AGENT_INDEX_ARCHIVE_URL"] = f"http://127.0.0.1:{server.server_port}/runtime.zip"
                try:
                    install = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                               "-File", str(installer), "-InstallGlobal"]
                    self.run_command(install, cwd=project, env=env)
                    runtime = project / ".agents" / "embedding-codebase"
                    self.assertTrue((runtime / "bin/agent-index.cmd").is_file())
                    self.assertFalse((runtime / "tests").exists())
                    source = project / "app"
                    source.mkdir()
                    (source / "example.py").write_text("def calculate_invoice_total():\n    return 42\n")
                    config = runtime / "index.config.json"
                    config.write_text(json.dumps({"exclude": ["ignored.txt"]}))
                    (project / "ignored.txt").write_text("excluded")
                    for command in (runtime / "bin/agent-index.cmd", root / "global bin/agent-index.cmd"):
                        self.run_command([str(command), "update"], cwd=source, env=env)
                        result = self.run_command([str(command), "search", "calculate invoice total"],
                                                  cwd=source, env=env)
                        self.assertIn("app/example.py", result.stdout)
                    index_path = runtime / "index/index.json"
                    self.assertEqual(set(json.loads(index_path.read_text())["files"]), {"app/example.py"})
                    before = index_path.read_bytes()
                    self.run_command(install, cwd=project, env=env)
                    self.assertEqual(index_path.read_bytes(), before)
                    self.assertEqual(json.loads(config.read_text()), {"exclude": ["ignored.txt"]})
                    failure = subprocess.run([str(runtime / "bin/agent-index.cmd"), "invalid-command"],
                                             cwd=source, env=env, capture_output=True, timeout=120)
                    self.assertNotEqual(failure.returncode, 0)
                finally:
                    if server:
                        server.shutdown()
                        server.server_close()


if __name__ == "__main__":
    unittest.main()
