"""Transparent, replaceable Phase-0 evidence and scoring rules."""

from .models import EvidenceMetrics, Project, RiskEvaluation


def calculate_evidence(project: Project) -> EvidenceMetrics:
    """Compare reported progress with schedule and spending.

    No visual estimate exists yet, so this is not visual verification.
    Schedule deviation means days past the planned end date, not a percent.
    """
    return EvidenceMetrics(
        progress_discrepancy=round(abs(project.planned_progress - project.reported_progress), 2),
        financial_progress_discrepancy=round(
            project.expenditure_percent - project.reported_progress, 2
        ),
        schedule_deviation=max((project.current_date - project.planned_end_date).days, 0),
    )


def evaluate_risk(project: Project) -> RiskEvaluation:
    """Compute illustrative 0–100 scores; these rules are not trained or calibrated."""
    evidence = calculate_evidence(project)
    progress_gap = evidence.progress_discrepancy
    spending_ahead = max(evidence.financial_progress_discrepancy, 0)
    overdue_component = min(evidence.schedule_deviation / 180, 1) * 30
    rainfall_component = min(project.rainfall_30d / 300, 1) * 10
    delay_risk = min(100.0, round(
        progress_gap * 0.4 + spending_ahead * 0.2 + overdue_component + rainfall_component, 2
    ))
    integrity = max(0.0, round(
        100 - progress_gap * 0.5 - spending_ahead * 0.3
        - min(evidence.schedule_deviation / 180, 1) * 20, 2
    ))
    explanation = (
        f"Reported progress differs from planned progress by {progress_gap:g} percentage points; "
        f"spending minus reported progress is {evidence.financial_progress_discrepancy:g} "
        f"percentage points; the planned end date is overdue by "
        f"{evidence.schedule_deviation} days. Rainfall over 30 days is "
        f"{project.rainfall_30d:g} mm. Scores are illustrative rule-based indicators, "
        "not validated predictions or image-derived findings."
    )
    return RiskEvaluation(
        project_id=project.project_id,
        evidence=evidence,
        delay_risk_score=delay_risk,
        integrity_score=integrity,
        explanation=explanation,
    )
