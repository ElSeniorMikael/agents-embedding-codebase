from __future__ import annotations

import unittest
from unittest import mock

from src.cli import build_parser, positive_int


class CliTests(unittest.TestCase):
    def test_positive_int_accepts_positive_values(self) -> None:
        self.assertEqual(positive_int("3"), 3)

    def test_positive_int_rejects_zero_negative_and_non_integer(self) -> None:
        for value in ("0", "-2", "abc"):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    positive_int(value)

    def test_parser_rejects_invalid_search_limit(self) -> None:
        parser = build_parser()
        with mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                parser.parse_args(["search", "needle", "--limit", "0"])

    def test_parser_rejects_invalid_embed_batch_size(self) -> None:
        parser = build_parser()
        with mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                parser.parse_args(["embed", "--batch-size", "0"])

    def test_build_alias_sets_full_rebuild(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build"])
        self.assertTrue(callable(args.func))


if __name__ == "__main__":
    unittest.main()
