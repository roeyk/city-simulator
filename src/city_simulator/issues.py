from __future__ import annotations

from city_simulator.fiscal import budget_basis, budget_deficit_severity, deficit_stress
from city_simulator.metrics import _labor_market
from city_simulator.state import CityState, Issue, ModelParameters, SignalLedger


def detect_issues(
    state: CityState,
    parameters: ModelParameters | None = None,
    signal_ledger: SignalLedger | None = None,
) -> list[Issue]:
    model_parameters = parameters or ModelParameters()
    ledger = signal_ledger or SignalLedger()
    issues: list[Issue] = []
    housing_gap = state.population / 2.35 - state.housing_units
    labor = _labor_market(
        population=state.population,
        demographics=state.demographics,
        jobs=state.jobs,
        infrastructure=state.infrastructure,
        education_profile=state.population_profile.get("education_percent", {}),
        parameters=model_parameters,
        sensitivity=state.sensitivity,
    )
    unemployment_rate = labor["unemployment_rate"]
    if housing_gap > state.population * 0.025:
        issues.append(
            Issue(
                code="housing_shortage",
                name="housing shortage",
                severity="high" if housing_gap > state.population * 0.05 else "medium",
                detail=f"{housing_gap:,.0f} more homes are needed.",
            )
        )
    if unemployment_rate > 0.08:
        issues.append(
            Issue(
                code="unemployment",
                name="unemployment",
                severity="high" if unemployment_rate > 0.13 else "medium",
                detail=f"{unemployment_rate:.1%} of the labor force is unemployed.",
            )
        )
    fiscal_stress = deficit_stress(
        state.budget,
        budget_basis(state, model_parameters),
    )
    if state.budget < 0:
        issues.append(
            Issue(
                code="budget_deficit",
                name="budget deficit",
                severity=budget_deficit_severity(fiscal_stress),
                detail=(
                    f"The city is ${abs(state.budget):,.0f} below balance, "
                    f"equal to {fiscal_stress:.1f}% of annual fiscal capacity."
                ),
            )
        )
    if fiscal_stress >= 18.0:
        issues.append(
            Issue(
                code="fiscal_crisis",
                name="fiscal crisis",
                severity="high",
                detail=(
                    "The deficit is large enough to threaten service continuity, "
                    "borrowing capacity, and public confidence."
                ),
            )
        )
    if state.infrastructure < 55:
        issues.append(
            Issue(
                code="aging_infrastructure",
                name="aging infrastructure",
                severity="high" if state.infrastructure < 40 else "medium",
                detail=f"Infrastructure condition is {state.infrastructure:.1f}/100.",
            )
        )
    if state.pollution > 58:
        issues.append(
            Issue(
                code="pollution",
                name="pollution",
                severity="high" if state.pollution > 72 else "medium",
                detail=f"Pollution is {state.pollution:.1f}/100.",
            )
        )
    if state.satisfaction < 45:
        issues.append(
            Issue(
                code="low_satisfaction",
                name="low satisfaction",
                severity="high" if state.satisfaction < 35 else "medium",
                detail=f"Resident satisfaction is {state.satisfaction:.1f}/100.",
            )
        )
    if state.demographics.low_income / max(state.population, 1.0) > 0.42:
        issues.append(
            Issue(
                code="income_stress",
                name="income stress",
                severity="medium",
                detail="More than 42% of residents are low income.",
            )
        )
    if ledger.get("healthcare_surge") >= 7.0 or ledger.get("grid_shortfall") >= 10.0:
        issues.append(
            Issue(
                code="seasonal_heat_cascade",
                name="seasonal heat cascade",
                severity="high" if ledger.get("healthcare_surge") >= 12.0 else "medium",
                detail=(
                    "Summer heat is stressing grid reliability, healthcare capacity, "
                    "and public trust."
                ),
            )
        )
    return issues
