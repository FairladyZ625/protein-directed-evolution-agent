"""Text timeline replay CLI for JSONL event streams."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

from .store import EventStore


def select_events(
    events: Iterable[Mapping[str, object]], round_id: int | None = None, strategy: str | None = None
) -> list[Mapping[str, object]]:
    return [
        event for event in events
        if (round_id is None or event["round_id"] == round_id)
        and (strategy is None or event["strategy"] == strategy)
    ]


def render_timeline(events: Iterable[Mapping[str, object]]) -> str:
    """Render a stable, one-event-per-line human-readable timeline."""
    return "\n".join(
        f"[{event['seq']}] {event['ts']} round={event['round_id']} strategy={event['strategy']} "
        f"{event['actor']} {event['event_type']} {json.dumps(event['payload'], sort_keys=True)}"
        for event in events
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay an AI4S event timeline")
    parser.add_argument("path", type=Path, help="path to events.jsonl")
    parser.add_argument("--round", dest="round_id", type=int)
    parser.add_argument("--strategy")
    args = parser.parse_args(argv)
    events = select_events(EventStore(args.path).iter_events(), args.round_id, args.strategy)
    timeline = render_timeline(events)
    if timeline:
        print(timeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
