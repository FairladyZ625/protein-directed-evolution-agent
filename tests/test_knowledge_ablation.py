from events.store import EventStore
from knowledge.ablation import _append_agent_trace


def test_agent_trace_replay_keeps_one_valid_event_chain(tmp_path):
    store = EventStore(tmp_path / "events.jsonl")
    report = {
        "tool_trace": [
            {
                "event_type": "agent.tool.analyze_measured",
                "round_id": 1,
                "strategy": "agent_no_knowledge",
                "actor": "data_analyst",
                "payload": {"n_measured": 10},
            },
            {
                "event_type": "agent.tool.test",
                "round_id": 2,
                "strategy": "agent_no_knowledge",
                "actor": "experiment",
                "payload": {"measured": 5},
            },
        ],
    }

    _append_agent_trace(store, report, seed=7)

    store.verify()
    events = list(store.iter_events())
    assert [event["seq"] for event in events] == [1, 2]
    assert all(event["payload"]["seed"] == 7 for event in events)
