from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from src.setup_ollama import main


class OllamaSetupTests(unittest.TestCase):
    def test_pulls_default_model_and_closes_server_context(self) -> None:
        server = mock.MagicMock()
        with mock.patch('src.setup_ollama.temporary_ollama_server', return_value=server), mock.patch(
            'src.setup_ollama.subprocess.run', return_value=subprocess.CompletedProcess([], 0)
        ) as run:
            self.assertEqual(main(), 0)
        run.assert_called_once_with(['ollama', 'pull', 'nomic-embed-text'], check=False)
        server.__exit__.assert_called_once()

    def test_download_failure_is_reported_and_server_context_closes(self) -> None:
        server = mock.MagicMock()
        server.__exit__.return_value = False
        with mock.patch('src.setup_ollama.temporary_ollama_server', return_value=server), mock.patch(
            'src.setup_ollama.subprocess.run', return_value=subprocess.CompletedProcess([], 1)
        ):
            with self.assertRaisesRegex(SystemExit, 'model download failed'):
                main()
        server.__exit__.assert_called_once()


if __name__ == '__main__':
    unittest.main()
