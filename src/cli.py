from __future__ import annotations

import argparse

from .commands import command_embed, command_search, command_status, command_update
from .config import (
    DEFAULT_EMBED_DIMENSIONS, DEFAULT_EMBED_MODEL, DEFAULT_EMBED_PROVIDER,
    DEFAULT_LEXICAL_WEIGHT, DEFAULT_SEMANTIC_WEIGHT, EMBED_BATCH_SIZE,
)

def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain a local agent project index.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    update = subcommands.add_parser("update", help="Incrementally refresh the index.")
    update.add_argument("--full", action="store_true", help="Rebuild from scratch.")
    update.set_defaults(func=command_update)

    build = subcommands.add_parser("build", help="Rebuild the index from scratch.")
    build.set_defaults(func=lambda args: command_update(argparse.Namespace(full=True)))

    status = subcommands.add_parser("status", help="Show index metadata.")
    status.set_defaults(func=command_status)

    search = subcommands.add_parser("search", help="Search indexed symbols and chunks.")
    search.add_argument("query")
    search.add_argument("--limit", type=positive_int, default=8)
    search.add_argument("--semantic", action="store_true", help="Rank chunks with cached semantic embeddings.")
    search.add_argument("--hybrid", action="store_true", help="Fuse lexical and semantic chunk rankings.")
    search.add_argument("--lexical-weight", type=float, default=DEFAULT_LEXICAL_WEIGHT, help="Hybrid lexical score weight.")
    search.add_argument("--semantic-weight", type=float, default=DEFAULT_SEMANTIC_WEIGHT, help="Hybrid semantic score weight.")
    search.add_argument("--auto-embed", action="store_true", help="Explicitly refresh missing or stale semantic embeddings before searching.")
    search.add_argument("--model", help="Override the embedding model used for the query.")
    search.add_argument("--provider", choices=("ollama", "openai"), help="Override the cached embedding provider.")
    search.set_defaults(func=command_search)

    embed = subcommands.add_parser("embed", help="Build semantic vector embeddings for indexed chunks.")
    embed.add_argument("--provider", choices=("ollama", "openai"), default=DEFAULT_EMBED_PROVIDER)
    embed.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    embed.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_EMBED_DIMENSIONS,
        help="Embedding dimensions; use 0 for the model default.",
    )
    embed.add_argument("--batch-size", type=positive_int, default=EMBED_BATCH_SIZE)
    embed.set_defaults(func=command_embed)
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
