"""Checkpointer adapter."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.base import BaseCheckpointSaver


def build_checkpointer(
    kind: str = "memory",
    database_url: str | None = None,
) -> BaseCheckpointSaver | None:
    """Return a LangGraph checkpointer.

    Memory is convenient for tests; SQLite provides durable local recovery.

    For SQLite:
    - pip install langgraph-checkpoint-sqlite
    - Use SqliteSaver with sqlite3.connect() and WAL mode
    - See: https://langchain-ai.github.io/langgraph/how-tos/persistence/
    """
    if kind == "none":
        return None
    if kind == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if kind == "sqlite":
        os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as exc:
            raise RuntimeError(
                "SQLite persistence requires: pip install langgraph-checkpoint-sqlite"
            ) from exc

        location = database_url or "outputs/checkpoints.sqlite"
        if location.startswith("sqlite:///"):
            location = location.removeprefix("sqlite:///")
        if location != ":memory:":
            path = Path(location)
            path.parent.mkdir(parents=True, exist_ok=True)
            location = str(path)
        connection = sqlite3.connect(location, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        return SqliteSaver(conn=connection)
    if kind == "postgres":
        raise RuntimeError("Postgres is optional; configure SQLite or memory for this lab")
    raise ValueError(f"Unknown checkpointer kind: {kind}")
