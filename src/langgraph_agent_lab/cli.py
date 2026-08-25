"""CLI for the lab."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Annotated, Any, cast
from uuid import uuid4

import typer
import yaml
from langchain_core.runnables import RunnableConfig

from .graph import build_graph
from .metrics import MetricsReport, metric_from_state, summarize_metrics, write_metrics
from .persistence import build_checkpointer
from .report import write_report
from .scenarios import load_scenarios
from .state import initial_state

app = typer.Typer(no_args_is_help=True)


@app.command("run-scenarios")
def run_scenarios(
    config: Annotated[Path, typer.Option("--config")],
    output: Annotated[Path, typer.Option("--output")],
) -> None:
    """Run all grading scenarios and write metrics JSON."""
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    scenarios = load_scenarios(cfg["scenarios_path"])
    checkpointer_kind = cfg.get("checkpointer", "memory")
    checkpointer = build_checkpointer(checkpointer_kind, cfg.get("database_url"))
    graph = build_graph(checkpointer=checkpointer)
    metrics = []
    persistence_evidence: list[dict[str, object]] = []
    persistence_checks: list[bool] = []
    for scenario in scenarios:
        state = initial_state(scenario)
        state["thread_id"] = f"{state['thread_id']}-{uuid4().hex[:8]}"
        run_config: RunnableConfig = {"configurable": {"thread_id": state["thread_id"]}}
        started = perf_counter()
        final_state = cast(dict[str, Any], graph.invoke(state, config=run_config))
        elapsed_ms = round((perf_counter() - started) * 1000)
        metric = metric_from_state(
            final_state,
            scenario.expected_route.value,
            scenario.requires_approval,
        )
        metric.latency_ms = elapsed_ms
        metrics.append(metric)
        history_count = len(list(graph.get_state_history(run_config))) if checkpointer else 0
        latest_snapshot = graph.get_state(run_config) if checkpointer else None
        latest_values = cast(dict[str, Any], getattr(latest_snapshot, "values", {}))
        persisted_event_nodes = [
            event.get("node") for event in latest_values.get("events", [])
        ]
        state_readback_verified = (
            history_count > 0
            and latest_values.get("route") == final_state.get("route")
            and "finalize" in persisted_event_nodes
        )
        persistence_checks.append(state_readback_verified)
        persistence_evidence.append(
            {
                "scenario_id": scenario.id,
                "thread_id": state["thread_id"],
                "checkpoint_count": history_count,
                "state_readback_verified": state_readback_verified,
                "finalize_persisted": "finalize" in persisted_event_nodes,
            }
        )
    report = summarize_metrics(metrics)
    report.resume_success = checkpointer_kind == "sqlite" and all(
        persistence_checks
    )
    write_metrics(report, output)
    evidence_path = Path(cfg.get("persistence_evidence_path", "outputs/persistence_evidence.json"))
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(persistence_evidence, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    diagram_path = Path(cfg.get("diagram_path", "outputs/graph.mmd"))
    diagram_path.parent.mkdir(parents=True, exist_ok=True)
    diagram_path.write_text(graph.get_graph().draw_mermaid(), encoding="utf-8")
    if cfg.get("report_path"):
        write_report(report, cfg["report_path"])
    typer.echo(f"Wrote metrics to {output}")
    typer.echo(f"Wrote persistence evidence to {evidence_path}")
    typer.echo(f"Wrote graph diagram to {diagram_path}")


@app.command("validate-metrics")
def validate_metrics(metrics: Annotated[Path, typer.Option("--metrics")]) -> None:
    """Validate metrics JSON schema for grading."""
    payload = json.loads(metrics.read_text(encoding="utf-8"))
    report = MetricsReport.model_validate(payload)
    if report.total_scenarios < 6:
        raise typer.BadParameter("Expected at least 6 scenarios")
    typer.echo(f"Metrics valid. success_rate={report.success_rate:.2%}")


if __name__ == "__main__":
    app()
