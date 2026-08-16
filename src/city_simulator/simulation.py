from __future__ import annotations

from city_simulator.derived import _clamp
from city_simulator.metrics import _city_metrics, _labor_market
from city_simulator.pressures import (
    _delayed_effects_from_pressures,
    _seasonal_pressure_ledger,
)
from city_simulator.state import (
    CityPolicy,
    CitySensitivity,
    CityState,
    DelayedEffect,
    Demographics,
    ExternalControls,
    Issue,
    ModelParameters,
    PressureLedger,
    YearResult,
)


def simulate(
    initial_state: CityState,
    policy: CityPolicy,
    years: int,
    external: ExternalControls | None = None,
    parameters: ModelParameters | None = None,
) -> list[YearResult]:
    if years < 0:
        raise ValueError("years must be non-negative")

    state = initial_state
    results: list[YearResult] = []
    external_controls = external or ExternalControls()
    model_parameters = parameters or ModelParameters()
    for _ in range(years):
        result = advance_year(state, policy, external_controls, model_parameters)
        results.append(result)
        state = result.state
    return results


def advance_year(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls | None = None,
    parameters: ModelParameters | None = None,
) -> YearResult:
    _validate_policy(policy)
    external_controls = external or ExternalControls()
    model_parameters = parameters or ModelParameters()
    previous_issues = detect_issues(state, model_parameters)

    intergovernmental_funding = (
        external_controls.county_funding
        + external_controls.state_funding
        + external_controls.federal_funding
    )
    revenue = _tax_base(state) * policy.tax_rate + intergovernmental_funding
    financing_cost = (
        max(state.budget, 0.0)
        * max(external_controls.national_interest_rate, 0.0)
        * model_parameters.financing_cost_budget_share
    )
    expenses = (
        policy.housing_investment
        + policy.transit_investment
        + policy.services_investment
        + policy.environment_investment
        + policy.business_support
        + state.population * model_parameters.resident_service_cost_per_person
        + financing_cost
    )
    budget = state.budget + revenue - expenses

    housing_units = state.housing_units + _housing_units_added(
        policy,
        external_controls,
        model_parameters,
        state.sensitivity,
    )
    jobs_delta = _jobs_delta(state, policy, external_controls, model_parameters)
    jobs = max(0.0, state.jobs + jobs_delta)

    infrastructure = _clamp(
        state.infrastructure
        - model_parameters.infrastructure_annual_wear
        + policy.transit_investment
        / model_parameters.transit_investment_per_infrastructure_point
        + policy.services_investment
        / model_parameters.services_investment_per_infrastructure_point,
        0.0,
        100.0,
    )
    pollution = _clamp(
        state.pollution
        + state.population / model_parameters.pollution_population_divisor
        + max(jobs_delta, 0.0) / model_parameters.pollution_jobs_divisor
        - (policy.environment_investment + external_controls.state_environment_mandate)
        / model_parameters.environment_spending_per_pollution_point,
        0.0,
        100.0,
    )

    housing_gap = state.population / 2.35 - housing_units
    pressure_ledger = _seasonal_pressure_ledger(
        state=state,
        policy=policy,
        infrastructure=infrastructure,
        pollution=pollution,
    )
    satisfaction = _satisfaction(
        state,
        policy,
        external_controls,
        infrastructure,
        pollution,
        housing_gap,
        model_parameters,
        state.sensitivity,
    )
    population_delta = _population_delta(
        state,
        policy,
        satisfaction,
        housing_gap,
        external_controls,
        model_parameters,
    )
    population = max(0.0, state.population + population_delta)
    demographics = _advance_demographics(state, policy, population, population_delta)
    growth_rate = population_delta / max(state.population, 1.0)

    next_state = CityState(
        year=state.year + 1,
        population=population,
        demographics=demographics,
        population_profile=state.population_profile,
        cohort_profiles=state.cohort_profiles,
        physical_profile=state.physical_profile,
        civic_assets=state.civic_assets,
        neighborhoods=state.neighborhoods,
        place_assets=state.place_assets,
        housing_stock=state.housing_stock,
        housing_assistance=state.housing_assistance,
        housing_units=housing_units,
        jobs=jobs,
        budget=budget,
        infrastructure=infrastructure,
        pollution=pollution,
        satisfaction=satisfaction,
        metrics=_city_metrics(
            state=state,
            population=population,
            demographics=demographics,
            jobs=jobs,
            jobs_delta=jobs_delta,
            housing_units=housing_units,
            housing_gap=housing_gap,
            satisfaction=satisfaction,
            infrastructure=infrastructure,
            pollution=pollution,
            growth_rate=growth_rate,
            parameters=model_parameters,
            sensitivity=state.sensitivity,
            pressure_ledger=pressure_ledger,
        ),
        sensitivity=state.sensitivity,
        pending_effects=_advance_delayed_effects(state.pending_effects)
        + _delayed_effects_from_pressures(pressure_ledger),
    )
    active_issues = detect_issues(next_state, model_parameters, pressure_ledger)
    return YearResult(
        year=next_state.year,
        state=next_state,
        revenue=revenue,
        expenses=expenses,
        population_delta=population_delta,
        jobs_delta=jobs_delta,
        housing_gap=housing_gap,
        active_issues=active_issues,
        overcome_issues=_overcome_issues(previous_issues, active_issues),
        pressure_ledger=pressure_ledger,
    )


def detect_issues(
    state: CityState,
    parameters: ModelParameters | None = None,
    pressure_ledger: PressureLedger | None = None,
) -> list[Issue]:
    model_parameters = parameters or ModelParameters()
    ledger = pressure_ledger or PressureLedger()
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
    if state.budget < 0:
        issues.append(
            Issue(
                code="budget_deficit",
                name="budget deficit",
                severity="high",
                detail=f"The city is ${abs(state.budget):,.0f} below balance.",
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




def _advance_delayed_effects(effects: tuple[DelayedEffect, ...]) -> tuple[DelayedEffect, ...]:
    advanced: list[DelayedEffect] = []
    for effect in effects:
        next_effect = effect.advance()
        if next_effect is not None:
            advanced.append(next_effect)
    return tuple(advanced)



def _validate_policy(policy: CityPolicy) -> None:
    if not 0.0 <= policy.tax_rate <= 1.0:
        raise ValueError("tax_rate must be between 0.0 and 1.0")
    rates = {
        "citizen_influx_rate": policy.citizen_influx_rate,
        "citizen_outflux_rate": policy.citizen_outflux_rate,
    }
    for name, value in rates.items():
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    bounded = {
        "zoning_restrictiveness": policy.zoning_restrictiveness,
        "permitting_speed": policy.permitting_speed,
        "development_restriction": policy.development_restriction,
    }
    for name, value in bounded.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0.0 and 1.0")
    investments = (
        policy.housing_investment,
        policy.transit_investment,
        policy.services_investment,
        policy.environment_investment,
        policy.business_support,
    )
    if any(value < 0 for value in investments):
        raise ValueError("investments must be non-negative")


def _housing_units_added(
    policy: CityPolicy,
    external: ExternalControls,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> float:
    buildable_share = _clamp(
        1.0
        - policy.zoning_restrictiveness
        * parameters.zoning_housing_drag
        * sensitivity.satisfaction_housing
        - policy.development_restriction * parameters.development_housing_drag
        + policy.permitting_speed * parameters.permitting_housing_bonus,
        0.15,
        1.25,
    )
    return (
        policy.housing_investment + external.county_housing_directive
    ) / parameters.housing_unit_cost * buildable_share


def _tax_base(state: CityState) -> float:
    income_base = (
        state.demographics.low_income * 16_000
        + state.demographics.middle_income * 34_000
        + state.demographics.high_income * 72_000
    )
    return income_base + state.jobs * 19_000


def _jobs_delta(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls,
    parameters: ModelParameters,
) -> float:
    business_effect = policy.business_support / parameters.business_support_per_job
    infrastructure_effect = (
        state.infrastructure - 50.0
    ) * parameters.infrastructure_jobs_multiplier
    tax_drag = max(policy.tax_rate - 0.2, 0.0) * parameters.high_tax_job_drag_multiplier
    restriction_drag = (
        policy.development_restriction * parameters.development_job_drag_multiplier
    )
    national_drag = (
        external.national_unemployment_pressure
        * parameters.national_unemployment_job_drag_multiplier
    )
    return business_effect + infrastructure_effect - tax_drag - restriction_drag - national_drag


def _advance_demographics(
    state: CityState,
    policy: CityPolicy,
    population: float,
    population_delta: float,
) -> Demographics:
    previous = state.demographics
    children = previous.children * 0.965 + max(population_delta, 0.0) * 0.18
    seniors = previous.seniors * 1.025 + previous.working_age * 0.012
    working_age = max(population - children - seniors, 0.0)

    upward_mobility = (
        policy.business_support / 150_000_000
        + policy.services_investment / 220_000_000
    )
    tax_pressure = max(policy.tax_rate - 0.2, 0.0) * 0.08
    low_share = _clamp(
        previous.low_income / max(previous.total, 1.0) - upward_mobility * 0.02 + tax_pressure,
        0.18,
        0.55,
    )
    high_share = _clamp(
        previous.high_income / max(previous.total, 1.0)
        + upward_mobility * 0.012
        - tax_pressure * 0.35,
        0.08,
        0.32,
    )
    middle_share = max(0.0, 1.0 - low_share - high_share)
    return Demographics(
        children=children,
        working_age=working_age,
        seniors=seniors,
        low_income=population * low_share,
        middle_income=population * middle_share,
        high_income=population * high_share,
    )


def _satisfaction(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls,
    infrastructure: float,
    pollution: float,
    housing_gap: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> float:
    service_score = (
        policy.services_investment + external.state_service_mandate
    ) / max(state.population, 1.0) / parameters.service_satisfaction_divisor
    tax_penalty = (
        policy.tax_rate * parameters.tax_satisfaction_penalty * sensitivity.satisfaction_tax
    )
    housing_penalty = (
        max(housing_gap, 0.0)
        / parameters.housing_satisfaction_divisor
        * sensitivity.satisfaction_housing
    )
    restriction_penalty = (
        policy.zoning_restrictiveness * parameters.zoning_satisfaction_penalty
        + policy.development_restriction * parameters.development_satisfaction_penalty
    )
    budget_penalty = parameters.budget_deficit_satisfaction_penalty if state.budget < 0 else 0.0
    raw = (
        parameters.base_satisfaction
        + infrastructure * parameters.infrastructure_satisfaction_bonus
        + service_score
        - pollution * parameters.pollution_satisfaction_penalty
    )
    return _clamp(
        raw - tax_penalty - housing_penalty - restriction_penalty - budget_penalty,
        0.0,
        100.0,
    )


def _population_delta(
    state: CityState,
    policy: CityPolicy,
    satisfaction: float,
    housing_gap: float,
    external: ExternalControls,
    parameters: ModelParameters,
) -> float:
    growth_rate = (
        satisfaction - parameters.base_satisfaction
    ) / parameters.satisfaction_growth_divisor
    housing_drag = max(housing_gap, 0.0) / parameters.housing_population_drag_divisor
    migration_rate = policy.citizen_influx_rate - policy.citizen_outflux_rate
    tax_migration_drag = max(policy.tax_rate - 0.22, 0.0) * parameters.high_tax_migration_drag
    restriction_drag = (
        policy.zoning_restrictiveness * parameters.zoning_migration_drag
        + policy.development_restriction * parameters.development_migration_drag
    )
    return state.population * (
        growth_rate
        - housing_drag
        + migration_rate
        + external.federal_growth_pressure
        - tax_migration_drag
        - restriction_drag
    )



def _overcome_issues(previous: list[Issue], current: list[Issue]) -> list[Issue]:
    current_codes = {issue.code for issue in current}
    return [issue for issue in previous if issue.code not in current_codes]
