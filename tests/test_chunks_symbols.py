from __future__ import annotations

import unittest

from src.chunk_utils import make_chunk, split_chunks
from src.chunks import chunk_file_text
from src.code_chunks import python_code_chunks, typescript_code_chunks
from src.symbols import extract_symbols, generic_symbols, python_symbols


class ChunkTests(unittest.TestCase):
    def test_split_chunks_records_text_range_and_tokens(self) -> None:
        chunks = split_chunks("notes.txt", "alpha beta\nsecond line")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["start"], 1)
        self.assertEqual(chunks[0]["end"], 2)
        self.assertEqual(chunks[0]["tokens"]["alpha"], 1)

    def test_make_chunk_ignores_blank_ranges(self) -> None:
        self.assertIsNone(make_chunk("empty.txt", ["", "   "], 1, 2))

    def test_python_code_chunks_include_module_and_symbol_chunks(self) -> None:
        text = "import os\n\nclass Greeter:\n    def hello(self):\n        return 'hi'\n"
        chunks = python_code_chunks("sample.py", text)
        kinds = {chunk["kind"] for chunk in chunks}
        self.assertIn("python-module", kinds)
        self.assertIn("python-symbol-group", kinds)

    def test_python_code_chunks_fallback_on_syntax_error(self) -> None:
        self.assertEqual(python_code_chunks("bad.py", "def nope(:\n"), [])

    def test_typescript_code_chunks_split_symbols(self) -> None:
        text = "import x from 'x';\nexport function run() {\n  return x;\n}\nconst value = 1;\n"
        chunks = typescript_code_chunks("app.ts", text)
        self.assertEqual(chunks[0]["kind"], "ts-module")
        self.assertTrue(any(chunk["kind"] == "ts-symbol" for chunk in chunks))

    def test_chunk_file_text_uses_language_aware_chunks_when_available(self) -> None:
        chunks = chunk_file_text("sample.py", "def hello():\n    return 1\n")
        self.assertEqual(chunks[0]["kind"], "python-symbol-group")


class SymbolTests(unittest.TestCase):
    def test_python_symbols_include_nested_functions(self) -> None:
        symbols = python_symbols("sample.py", "class A:\n    def method(self):\n        pass\n")
        self.assertEqual([symbol["name"] for symbol in symbols], ["A", "method"])

    def test_generic_symbols_extract_typescript_routes_and_constants(self) -> None:
        text = "app.get('/health', handler)\nexport const answer = 42\n"
        symbols = generic_symbols("server.ts", text)
        names = {symbol["name"] for symbol in symbols}
        self.assertIn("GET /health", names)
        self.assertIn("answer", names)

    def test_generic_symbols_extract_css_markdown_and_sql(self) -> None:
        self.assertEqual(generic_symbols("style.css", ".button { color: red }")[0]["name"], ".button")
        self.assertEqual(generic_symbols("README.md", "## Install\n")[0]["name"], "Install")
        self.assertEqual(generic_symbols("schema.sql", "create table users (id int);")[0]["name"], "users")

    def test_extract_symbols_dispatches_by_suffix(self) -> None:
        self.assertEqual(extract_symbols("sample.py", "def run():\n    pass\n")[0]["kind"], "function")
        self.assertEqual(extract_symbols("README.md", "# Title\n")[0]["kind"], "h1")


if __name__ == "__main__":
    unittest.main()
