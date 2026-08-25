"""Node functions for the LangGraph workflow.

Each function receives AgentState and returns a partial state update dict.
Do NOT mutate input state — return new values only.

LLM REQUIREMENT:
- classify_node MUST use a real LLM call (structured output for intent classification)
- answer_node MUST use a real LLM call (grounded response generation)
- evaluate_node SHOULD use LLM-as-judge (bonus points; heuristic acceptable for base score)
"""

from __future__ import annotations

import os
from typing import Literal, cast

from pydantic import BaseModel, Field

from .llm import get_llm
from .state import AgentState, ApprovalDecision, make_event


class RouteDecision(BaseModel):
    """Structured classifier response used to make routing deterministic."""

    route: Literal["simple", "tool", "missing_info", "risky", "error"]
    rationale: str = Field(description="Short reason based only on the user's request")


class ToolEvaluation(BaseModel):
    """Structured LLM-as-judge response for the tool quality gate."""

    result: Literal["success", "needs_retry"]
    rationale: str = Field(description="Short evidence-based quality assessment")


# ─── EXAMPLE: working node (provided for reference) ──────────────────
def intake_node(state: AgentState) -> dict:
    """Normalize raw query. This node is provided as a working example."""
    query = state.get("query", "").strip()
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }


def classify_node(state: AgentState) -> dict[str, object]:
    """Classify the query into a route using an LLM.

    *** MUST use a real LLM call — keyword-only heuristics will lose points. ***

    Use .with_structured_output() or equivalent to get reliable enum classification.
    The LLM should classify into one of: simple, tool, missing_info, risky, error.

    Hints:
    - See llm.py for the get_llm() helper
    - Use Pydantic model or TypedDict with .with_structured_output()
    - Set risk_level to "high" for risky routes, "low" otherwise
    - Priority guide: risky > tool > missing_info > error > simple

    Return: {"route": str, "risk_level": str, "events": [make_event(...)]}
    """
    classifier = get_llm(temperature=0).with_structured_output(RouteDecision)
    decision = cast(
        RouteDecision,
        classifier.invoke(
            [
                (
                    "system",
                    "You route support tickets. Return exactly one route. Apply this priority "
                    "when more than one intent appears: "
                    "risky > tool > missing_info > error > simple. "
                    "risky means a requested side effect such as refund, deletion, cancellation, "
                    "account change, or sending a message. tool means a read-only "
                    "lookup or search. "
                    "missing_info means the request is too vague to act on safely. error means the "
                    "user reports a timeout, crash, unavailable service, or processing failure. "
                    "Never infer an error merely from vague verbs such as fix, help, or resolve: "
                    "without an affected object, symptom, or error detail, use missing_info. "
                    "Use error only when an operational failure symptom is explicitly stated. "
                    "simple means a general support question answerable without a tool. "
                    "Examples: 'Please help with it' is missing_info; 'the service timed out' "
                    "is error; 'how do I change my password?' is simple.",
                ),
                ("human", f"Classify this support request:\n{state.get('query', '')}"),
            ]
        ),
    )
    route = decision.route
    return {
        "route": route,
        "risk_level": "high" if route == "risky" else "low",
        "events": [
            make_event(
                "classify",
                "completed",
                "LLM structured classification completed",
                route=route,
                rationale=decision.rationale,
            )
        ],
    }


def tool_node(state: AgentState) -> dict[str, object]:
    """Execute a mock tool call.

    Simulate transient failures for error-route scenarios to test retry loops.

    Requirements:
    - Read current attempt count from state
    - If route is "error" and attempt < 2: return error result (string containing "ERROR")
    - Otherwise: return a mock success result string
    - Append result to tool_results list

    Return: {"tool_results": [result_string], "events": [make_event(...)]}
    """
    attempt = int(state.get("attempt", 0))
    route = state.get("route", "")
    if route == "error" and attempt < 2:
        result = f"ERROR: transient support service failure on attempt {attempt}"
        event_type = "failed"
    elif route == "risky":
        proposed_action = state.get("proposed_action") or state.get("query", "")
        result = f"SUCCESS: approved action completed: {proposed_action}"
        event_type = "completed"
    else:
        result = f"SUCCESS: support tool returned a result for: {state.get('query', '')}"
        event_type = "completed"
    return {
        "tool_results": [result],
        "events": [
            make_event(
                "tool",
                event_type,
                "mock support tool executed",
                attempt=attempt,
            )
        ],
    }


def evaluate_node(state: AgentState) -> dict[str, object]:
    """Evaluate tool results — the retry-loop gate.

    Check whether the latest tool result is satisfactory or needs retry.

    SHOULD use LLM-as-judge for bonus points. Heuristic (e.g., check for "ERROR" substring)
    is acceptable for base score.

    Requirements:
    - Read the latest entry from tool_results
    - Set evaluation_result to "needs_retry" or "success"
    - This field drives route_after_evaluate conditional edge

    Note: You may need to add 'evaluation_result' to AgentState if not present.

    Return: {"evaluation_result": str, "events": [make_event(...)]}
    """
    results = state.get("tool_results", [])
    latest = results[-1] if results else "ERROR: tool returned no result"
    explicit_error = "ERROR" in latest.upper()
    mode = "llm_judge"
    rationale = ""
    try:
        judge = get_llm(temperature=0).with_structured_output(ToolEvaluation)
        decision = cast(
            ToolEvaluation,
            judge.invoke(
                [
                    (
                        "system",
                        "Judge whether a support-tool result is usable. Any explicit ERROR, "
                        "timeout, empty result, or incomplete result needs_retry. "
                        "A concrete SUCCESS result is "
                        "success. Base the decision only on the supplied result.",
                    ),
                    ("human", latest),
                ]
            ),
        )
        result = decision.result
        rationale = decision.rationale
    except Exception as exc:
        mode = "deterministic_fallback"
        result = "needs_retry" if explicit_error else "success"
        rationale = f"LLM judge unavailable: {type(exc).__name__}"

    if explicit_error:
        result = "needs_retry"
    elif latest.upper().startswith("SUCCESS:"):
        result = "success"
    return {
        "evaluation_result": result,
        "events": [
            make_event(
                "evaluate",
                "completed",
                "tool result evaluated",
                result=result,
                mode=mode,
                rationale=rationale,
            )
        ],
    }


def answer_node(state: AgentState) -> dict[str, object]:
    """Generate a final response using an LLM.

    *** MUST use a real LLM call — hardcoded strings will lose points. ***

    The LLM should generate a helpful response grounded in available context:
    - tool_results (if any)
    - approval decision (if risky route)
    - original query

    Return: {"final_answer": str, "events": [make_event(...)]}
    """
    context = "\n".join(state.get("tool_results", [])) or "No tool result was needed."
    approval = state.get("approval")
    response = get_llm(temperature=0).invoke(
        [
            (
                "system",
                "You are a concise support agent. Answer the user using only the supplied support "
                "context and approval status. Do not invent order data, action outcomes, "
                "or private "
                "facts. When no tool was needed, give safe general guidance. Clearly distinguish a "
                "mock tool result from verified production data.",
            ),
            (
                "human",
                f"User request: {state.get('query', '')}\n"
                f"Tool context: {context}\n"
                f"Approval: {approval or 'not required'}",
            ),
        ]
    )
    content = response.content
    answer = content.strip() if isinstance(content, str) else str(content).strip()
    return {
        "final_answer": answer,
        "messages": [f"answer:{answer[:80]}"],
        "events": [make_event("answer", "completed", "LLM grounded answer generated")],
    }


def ask_clarification_node(state: AgentState) -> dict[str, object]:
    """Ask for missing information instead of hallucinating.

    Generate a specific clarification question based on the vague/incomplete query.

    Note: You may need to add 'pending_question' to AgentState if not present.

    Return: {"pending_question": str, "final_answer": str, "events": [make_event(...)]}
    """
    question = (
        "Could you provide the affected feature or service, what you expected to happen, "
        "what happened instead, and any error message?"
    )
    approval = state.get("approval")
    if approval is not None and not approval.get("approved"):
        question = "The proposed action was not approved. What safe alternative would you like?"
    return {
        "pending_question": question,
        "final_answer": question,
        "messages": [f"clarification:{question}"],
        "events": [make_event("clarify", "completed", "clarification requested")],
    }


def risky_action_node(state: AgentState) -> dict[str, object]:
    """Prepare a risky action for human approval.

    Describe the proposed action and why it requires approval.

    Note: You may need to add 'proposed_action' to AgentState if not present.

    Return: {"proposed_action": str, "events": [make_event(...)]}
    """
    proposed_action = (
        f"Execute the requested side effect after human verification: {state.get('query', '')}"
    )
    return {
        "proposed_action": proposed_action,
        "events": [
            make_event(
                "risky_action",
                "approval_required",
                "risky action prepared but not executed",
            )
        ],
    }


def approval_node(state: AgentState) -> dict[str, object]:
    """Human-in-the-loop approval step.

    Default behavior: mock approval (approved=True) so tests and CI run offline.
    Extension: if env LANGGRAPH_INTERRUPT=true, use langgraph.types.interrupt() for real HITL.

    Return approval metadata and an audit event.
    """
    use_interrupt = os.getenv("LANGGRAPH_INTERRUPT", "false").lower() == "true"
    if use_interrupt:
        from langgraph.types import interrupt

        raw_decision = interrupt(
            {
                "type": "approval_required",
                "scenario_id": state.get("scenario_id"),
                "proposed_action": state.get("proposed_action"),
            }
        )
        if isinstance(raw_decision, bool):
            decision = ApprovalDecision(
                approved=raw_decision,
                reviewer="human",
                comment="Resumed from LangGraph interrupt",
            )
        else:
            decision = ApprovalDecision.model_validate(raw_decision)
        mode = "interrupt"
    else:
        decision = ApprovalDecision(
            approved=True,
            reviewer="mock-reviewer",
            comment="Lab default; replace with an authorized reviewer in production",
        )
        mode = "mock"
    return {
        "approval": decision.model_dump(),
        "events": [
            make_event(
                "approval",
                "completed",
                "approval decision recorded",
                approved=decision.approved,
                mode=mode,
            )
        ],
    }


def retry_or_fallback_node(state: AgentState) -> dict[str, object]:
    """Record a retry attempt.

    Increment the attempt counter and log the transient failure.

    Requirements:
    - Read current attempt from state, increment by 1
    - Add an error message to errors list
    - Return updated attempt count

    Return: {"attempt": int, "errors": [str], "events": [make_event(...)]}
    """
    attempt = int(state.get("attempt", 0)) + 1
    error = f"Transient failure recorded before retry attempt {attempt}"
    return {
        "attempt": attempt,
        "errors": [error],
        "events": [make_event("retry", "scheduled", error, attempt=attempt)],
    }


def dead_letter_node(state: AgentState) -> dict[str, object]:
    """Handle unresolvable failures after max retries exceeded.

    This is the third layer: retry → fallback → dead letter.
    Log the failure and set a final_answer explaining that the request could not be completed.

    Return: {"final_answer": str, "events": [make_event(...)]}
    """
    answer = (
        "The request could not be completed within the retry limit. "
        "It has been moved to the support dead-letter queue for manual investigation."
    )
    return {
        "final_answer": answer,
        "events": [
            make_event(
                "dead_letter",
                "escalated",
                "retry limit exhausted",
                attempt=state.get("attempt", 0),
                max_attempts=state.get("max_attempts", 0),
            )
        ],
    }


def finalize_node(state: AgentState) -> dict[str, object]:
    """Emit a final audit event. All routes must pass through here before END.

    Return: {"events": [make_event("finalize", "completed", "workflow finished")]}
    """
    return {
        "events": [
            make_event(
                "finalize",
                "completed",
                "workflow finished",
                route=state.get("route", "unknown"),
            )
        ]
    }
