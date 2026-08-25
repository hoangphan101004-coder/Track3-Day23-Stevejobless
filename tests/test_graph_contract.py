"""Deterministic graph-contract probes for retry and approval boundaries."""

from langgraph_agent_lab import nodes
from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.metrics import metric_from_state
from langgraph_agent_lab.persistence import build_checkpointer
from langgraph_agent_lab.state import Route, Scenario, initial_state, make_event


def _classifier(route: Route):
    def classify(state):
        return {
            "route": route.value,
            "risk_level": "high" if route is Route.RISKY else "low",
            "events": [make_event("classify", "completed", "deterministic test route")],
        }

    return classify


def _event_nodes(result):
    return [event["node"] for event in result.get("events", [])]


def test_dead_letter_boundary_does_not_call_tool(monkeypatch):
    monkeypatch.setattr(nodes, "classify_node", _classifier(Route.ERROR))
    graph = build_graph(checkpointer=build_checkpointer("memory"))
    scenario = Scenario(
        id="dead-letter-contract",
        query="An operational failure occurred",
        expected_route=Route.ERROR,
        max_attempts=1,
    )
    state = initial_state(scenario)

    result = graph.invoke(
        state,
        config={"configurable": {"thread_id": state["thread_id"]}},
    )

    event_nodes = _event_nodes(result)
    assert event_nodes == ["intake", "classify", "retry", "dead_letter", "finalize"]
    assert result["attempt"] == 1
    assert "tool" not in event_nodes


def test_rejected_approval_routes_to_clarification_without_tool(monkeypatch):
    monkeypatch.setattr(nodes, "classify_node", _classifier(Route.RISKY))

    def reject_approval(state):
        return {
            "approval": {
                "approved": False,
                "reviewer": "contract-test-reviewer",
                "comment": "Rejected by deterministic contract test",
            },
            "events": [make_event("approval", "completed", "approval rejected")],
        }

    monkeypatch.setattr(nodes, "approval_node", reject_approval)
    graph = build_graph(checkpointer=build_checkpointer("memory"))
    scenario = Scenario(
        id="rejected-approval-contract",
        query="Delete the account",
        expected_route=Route.RISKY,
        requires_approval=True,
    )
    state = initial_state(scenario)

    result = graph.invoke(
        state,
        config={"configurable": {"thread_id": state["thread_id"]}},
    )

    event_nodes = _event_nodes(result)
    assert event_nodes == [
        "intake",
        "classify",
        "risky_action",
        "approval",
        "clarify",
        "finalize",
    ]
    assert "tool" not in event_nodes
    assert result["approval"]["approved"] is False
    assert result["pending_question"]

    metric = metric_from_state(result, expected_route="risky", approval_required=True)
    assert metric.success is True


def test_approval_metric_rejects_tool_before_approval():
    state = {
        "scenario_id": "invalid-approval-order",
        "route": "risky",
        "final_answer": "unsafe result",
        "approval": {"approved": True},
        "events": [
            make_event("tool", "completed", "tool ran too early"),
            make_event("approval", "completed", "approval arrived too late"),
            make_event("finalize", "completed", "workflow finished"),
        ],
        "errors": [],
    }

    metric = metric_from_state(state, expected_route="risky", approval_required=True)

    assert metric.approval_observed is True
    assert metric.success is False
