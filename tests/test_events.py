from __future__ import annotations

import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from events.project import EventProjector
from events.replay import render_timeline, select_events
from events.store import EventStore


def _append_examples(store: EventStore) -> None:
    store.append("thought.created", round_id=1, strategy="random", actor="planner", payload={"idea": "sample"}, ts="2026-09-11T00:00:00Z")
    store.append("proposal.validated", round_id=2, strategy="knowledge_agent", actor="validator", payload={"variant": "FWAA"}, ts="2026-09-11T00:00:01Z")


def test_append_hash_chain_and_verification(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    _append_examples(store)

    events = list(store.iter_events())
    assert [event["seq"] for event in events] == [1, 2]
    assert events[1]["prev_hash"] == events[0]["hash"]
    assert len(store.head_hash) == 64
    assert store.verify() is None


def test_concurrent_appends_keep_chain_intact(tmp_path):
    """An agentic LLM turn fires tool calls in parallel (pydantic-ai runs sync tools in
    an anyio thread pool), so append() must be safe under concurrency: no two events may
    share a seq and the hash chain must still verify."""
    store = EventStore(tmp_path / "events.jsonl")
    n = 200
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(
            lambda i: store.append("agent.tool.list_pool", round_id=1, strategy="agentic",
                                   actor="hypothesis_generator", payload={"i": i}),
            range(n)))

    seqs = [event["seq"] for event in store.iter_events()]
    assert seqs == list(range(1, n + 1))  # contiguous, no duplicates
    assert store.verify() is None


def test_append_fsyncs_before_returning(tmp_path, monkeypatch):
    synced: list[int] = []
    monkeypatch.setattr("events.store.os.fsync", synced.append)

    EventStore(tmp_path / "events.jsonl").append(
        "run.started", round_id=1, strategy="random", actor="campaign", payload={}
    )

    assert len(synced) == 1


def test_restart_discards_truncated_tail_before_appending(tmp_path):
    path = tmp_path / "events.jsonl"
    original = EventStore(path)
    original.append("run.started", round_id=1, strategy="random", actor="campaign", payload={})
    with path.open("ab") as stream:
        stream.write(b'{"seq":2')

    restarted = EventStore(path)
    appended = restarted.append(
        "run.finished", round_id=1, strategy="random", actor="campaign", payload={}
    )

    assert [event["seq"] for event in restarted.iter_events()] == [1, 2]
    assert appended["seq"] == 2
    assert restarted.verify() is None


def test_tampering_is_detected_at_changed_event(tmp_path):
    path = tmp_path / "events.jsonl"
    store = EventStore(path)
    _append_examples(store)
    path.write_text(path.read_text().replace("FWAA", "AAAA"), encoding="utf-8")

    with pytest.raises(ValueError, match="chain broken at seq=2"):
        store.verify()


def test_projection_rebuild_is_idempotent_and_readonly(tmp_path):
    event_path = tmp_path / "events.jsonl"
    _append_examples(EventStore(event_path))
    projector = EventProjector(event_path, tmp_path / "events.sqlite")

    assert projector.rebuild() == 2
    assert projector.rebuild() == 2
    with projector.connect_readonly() as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM v_proposals").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("INSERT INTO events VALUES (3, '', '', NULL, NULL, '', '', '', '')")


def test_replay_filters_and_renders_deterministically(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    _append_examples(store)

    selected = select_events(store.iter_events(), round_id=2, strategy="knowledge_agent")
    timeline = render_timeline(selected)
    assert len(selected) == 1
    assert "proposal.validated" in timeline
    assert "FWAA" in timeline


def test_replay_cli_applies_round_and_strategy_filters(tmp_path):
    path = tmp_path / "events.jsonl"
    _append_examples(EventStore(path))

    result = subprocess.run(
        [sys.executable, "-m", "events.replay", str(path), "--round", "2", "--strategy", "knowledge_agent"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "proposal.validated" in result.stdout
    assert "thought.created" not in result.stdout


def test_compressed_archive_reads_transparently_and_refuses_writes(tmp_path):
    """一次 campaign 轮次现在设计上千条候选,每个角色事件都带整个文库:未压缩流约 80MB、
    gzip 后约 3MB。归档流因此以 .gz 保存,读者仍传逻辑 .jsonl 路径。这条测试钉住三件事:
    透明回退读到的链与原始流逐事件一致、self.path 指向真正读的文件(证据链不撒谎)、
    以及往压缩档写入会被拒绝而不是静默破坏哈希链。"""
    import gzip

    raw = tmp_path / "stream.events.jsonl"
    writer = EventStore(raw)
    for index in range(3):
        writer.append("probe.event", round_id=index, strategy="probe", actor="test", payload={"i": index})
    writer.verify()
    baseline = list(writer.iter_events())
    head = writer.head_hash

    archive = tmp_path / "stream.events.jsonl.gz"
    archive.write_bytes(gzip.compress(raw.read_bytes()))
    raw.unlink()

    reader = EventStore(raw)  # 逻辑路径,原文件已不在
    assert reader.path == archive, "未透明回退到 .gz 归档"
    reader.verify()
    assert list(reader.iter_events()) == baseline
    assert reader.head_hash == head

    with pytest.raises(ValueError, match="compressed archive"):
        reader.append("probe.event", round_id=9, strategy="probe", actor="test", payload={})
