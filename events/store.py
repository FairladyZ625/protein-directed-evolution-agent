"""Append-only JSONL event storage with a tamper-evident hash chain."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("event_type", "round_id", "strategy", "actor", "payload")


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _event_hash(prev_hash: str, body: Mapping[str, Any]) -> str:
    return hashlib.sha256((prev_hash + _canonical(body)).encode("utf-8")).hexdigest()


class EventStore:
    """The campaign-owned writer for a single JSONL event stream.

    Readers should use :meth:`iter_events`; projection and replay modules never append.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._next_seq, self._last_hash = self._tail()
        # An agentic LLM turn can fire several tool calls at once; pydantic-ai runs the
        # sync tool functions in an anyio worker thread pool, so append() is called
        # concurrently. Serialise the read-tail / write / advance sequence or two events
        # collide on the same seq and prev_hash and break the chain.
        self._lock = threading.Lock()

    def _tail(self) -> tuple[int, str]:
        last: dict[str, Any] | None = None
        for last in self.iter_events():
            pass
        if last is None:
            return 1, ""
        return int(last["seq"]) + 1, str(last["hash"])

    def append(
        self,
        event_type: str,
        *,
        round_id: int | None,
        strategy: str | None,
        actor: str,
        payload: Mapping[str, Any] | None = None,
        ts: str | None = None,
    ) -> dict[str, Any]:
        """Durably append one event and return its complete stored representation."""
        if not event_type:
            raise ValueError("event_type is required")
        if not actor:
            raise ValueError("actor is required")
        with self._lock:
            body: dict[str, Any] = {
                "seq": self._next_seq,
                "ts": ts or datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "event_type": event_type,
                "round_id": round_id,
                "strategy": strategy,
                "actor": actor,
                "payload": dict(payload or {}),
            }
            event = {
                **body,
                "prev_hash": self._last_hash,
                "hash": _event_hash(self._last_hash, body),
            }
            encoded = (_canonical(event) + "\n").encode("utf-8")
            with self.path.open("ab") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            self._next_seq += 1
            self._last_hash = event["hash"]
            return event

    def iter_events(self) -> Iterator[dict[str, Any]]:
        """Yield complete JSONL records, tolerating an interrupted final write."""
        if not self.path.exists():
            return
        with self.path.open("rb") as stream:
            for line in stream:
                if not line.endswith(b"\n"):
                    break
                yield json.loads(line)

    def verify(self) -> None:
        """Raise ``ValueError`` at the first broken link or malformed complete record."""
        prev_hash = ""
        expected_seq = 1
        for event in self.iter_events():
            seq = event.get("seq")
            if seq != expected_seq:
                raise ValueError(f"chain broken at seq={seq}")
            if any(field not in event for field in REQUIRED_FIELDS):
                raise ValueError(f"chain broken at seq={seq}")
            body = {key: event.get(key) for key in ("seq", "ts", *REQUIRED_FIELDS)}
            if event.get("prev_hash") != prev_hash or event.get("hash") != _event_hash(prev_hash, body):
                raise ValueError(f"chain broken at seq={seq}")
            prev_hash = event["hash"]
            expected_seq += 1

    @property
    def head_hash(self) -> str:
        """Return the chain head suitable for anchoring in a commit or release record."""
        return self._last_hash
