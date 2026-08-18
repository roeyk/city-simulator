from __future__ import annotations

from typing import TypeVar

from city_simulator.derived import _clamp, _service_coverage
from city_simulator.metrics import (
    _city_metrics,
    _crime,
    _labor_market,
    _public_sentiment,
    _sentiment_signals,
)
from city_simulator.signals import (
    SignalContext,
    _delayed_effects_from_signals,
    signal_ledger_for_turn,
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
    SignalLedger,
    YearResult,
)
from city_simulator.turn_steps import AnnualTurnContext, TurnStep, run_turn_steps

T = TypeVar("T")


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
    external_controls = external or ExternalControls()
    model_parameters = parameters or ModelParameters()
    context = run_turn_steps(
        AnnualTurnContext(
            state=state,
            policy=policy,
            external=external_controls,
            parameters=model_parameters,
        ),
        ANNUAL_TURN_STEPS,
    )

    return YearResult(
        year=_required(context.next_state, "next_state").year,
        state=_required(context.next_state, "next_state"),
        revenue=_required(context.revenue, "revenue"),
        expenses=_required(context.expenses, "expenses"),
        population_delta=_required(context.population_delta, "population_delta"),
        jobs_delta=_required(context.jobs_delta, "jobs_delta"),
        housing_gap=_required(context.housing_gap, "housing_gap"),
        active_issues=context.active_issues,
        overcome_issues=_overcome_issues(context.previous_issues, context.active_issues),
        signal_ledger=_required(context.signal_ledger, "signal_ledger"),
    )


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
    if not 0.0 <= policy.business_tax_rate <= 1.0:
        raise ValueError("business_tax_rate must be between 0.0 and 1.0")
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
    return _resident_tax_base(state) + _business_tax_base(state)


def _resident_tax_base(state: CityState) -> float:
    return (
        state.demographics.low_income * 16_000
        + state.demographics.middle_income * 34_000
        + state.demographics.high_income * 72_000
    )


def _business_tax_base(state: CityState) -> float:
    return state.jobs * 19_000


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
    tax_drag = max(policy.business_tax_rate - 0.10, 0.0) * parameters.high_tax_job_drag_multiplier
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


def _required(value: T | None, name: str) -> T:
    if value is None:
        raise RuntimeError(f"annual turn step did not produce {name}")
    return value


def _step_validate_inputs(context: AnnualTurnContext) -> None:
    _validate_policy(context.policy)
    context.previous_issues = detect_issues(context.state, context.parameters)


def _step_local_fiscal_policy(context: AnnualTurnContext) -> None:
    intergovernmental_funding = (
        context.external.county_funding
        + context.external.state_funding
        + context.external.federal_funding
    )
    context.revenue = _annual_revenue(context.state, context.policy) + intergovernmental_funding
    financing_cost = (
        max(context.state.budget, 0.0)
        * max(context.external.national_interest_rate, 0.0)
        * context.parameters.financing_cost_budget_share
    )
    context.expenses = _annual_expenses(context.state, context.policy, context.parameters) + financing_cost
    context.budget = context.state.budget + context.revenue - context.expenses


def _annual_revenue(state: CityState, policy: CityPolicy) -> float:
    source_total = state.revenue_sources.total
    if source_total > 0:
        default_policy = CityPolicy()
        return (
            source_total
            + _resident_tax_base(state) * (policy.tax_rate - default_policy.tax_rate)
            + _business_tax_base(state)
            * (policy.business_tax_rate - default_policy.business_tax_rate)
        )
    if state.annual_income > 0:
        default_policy = CityPolicy()
        return (
            state.annual_income
            + _resident_tax_base(state) * (policy.tax_rate - default_policy.tax_rate)
            + _business_tax_base(state)
            * (policy.business_tax_rate - default_policy.business_tax_rate)
        )
    return (
        _resident_tax_base(state) * policy.tax_rate
        + _business_tax_base(state) * policy.business_tax_rate
    )


def _annual_expenses(
    state: CityState,
    policy: CityPolicy,
    parameters: ModelParameters,
) -> float:
    if state.annual_budget > 0:
        return state.annual_budget
    return (
        policy.housing_investment
        + policy.transit_investment
        + policy.services_investment
        + policy.environment_investment
        + policy.business_support
        + state.population * parameters.resident_service_cost_per_person
    )


def _step_development_and_jobs(context: AnnualTurnContext) -> None:
    context.housing_units = context.state.housing_units + _housing_units_added(
        context.policy,
        context.external,
        context.parameters,
        context.state.sensitivity,
    )
    context.jobs_delta = _jobs_delta(
        context.state,
        context.policy,
        context.external,
        context.parameters,
    )
    context.jobs = max(0.0, context.state.jobs + context.jobs_delta)


def _step_infrastructure_environment(context: AnnualTurnContext) -> None:
    jobs_delta = _required(context.jobs_delta, "jobs_delta")
    context.infrastructure = _clamp(
        context.state.infrastructure
        - context.parameters.infrastructure_annual_wear
        + context.policy.transit_investment
        / context.parameters.transit_investment_per_infrastructure_point
        + context.policy.services_investment
        / context.parameters.services_investment_per_infrastructure_point,
        0.0,
        100.0,
    )
    context.pollution = _clamp(
        context.state.pollution
        + context.state.population / context.parameters.pollution_population_divisor
        + max(jobs_delta, 0.0) / context.parameters.pollution_jobs_divisor
        - (context.policy.environment_investment + context.external.state_environment_mandate)
        / context.parameters.environment_spending_per_pollution_point,
        0.0,
        100.0,
    )


def _step_seasonal_signals(context: AnnualTurnContext) -> None:
    context.housing_gap = context.state.population / 2.35 - _required(
        context.housing_units,
        "housing_units",
    )
    context.signal_ledger = signal_ledger_for_turn(
        SignalContext(
            state=context.state,
            policy=context.policy,
            infrastructure=_required(context.infrastructure, "infrastructure"),
            pollution=_required(context.pollution, "pollution"),
        )
    )


def _step_satisfaction_migration_demographics(context: AnnualTurnContext) -> None:
    context.satisfaction = _satisfaction(
        context.state,
        context.policy,
        context.external,
        _required(context.infrastructure, "infrastructure"),
        _required(context.pollution, "pollution"),
        _required(context.housing_gap, "housing_gap"),
        context.parameters,
        context.state.sensitivity,
    )
    context.population_delta = _population_delta(
        context.state,
        context.policy,
        context.satisfaction,
        _required(context.housing_gap, "housing_gap"),
        context.external,
        context.parameters,
    )
    context.population = max(0.0, context.state.population + context.population_delta)
    context.demographics = _advance_demographics(
        context.state,
        context.policy,
        context.population,
        context.population_delta,
    )
    context.growth_rate = context.population_delta / max(context.state.population, 1.0)


def _step_labor_market(context: AnnualTurnContext) -> None:
    context.labor_market = _labor_market(
        population=_required(context.population, "population"),
        demographics=_required(context.demographics, "demographics"),
        jobs=_required(context.jobs, "jobs"),
        infrastructure=_required(context.infrastructure, "infrastructure"),
        education_profile=context.state.population_profile.get("education_percent", {}),
        parameters=context.parameters,
        sensitivity=context.state.sensitivity,
    )


def _step_sentiment(context: AnnualTurnContext) -> None:
    population = _required(context.population, "population")
    labor_market = _required(context.labor_market, "labor_market")
    housing_pressure = max(_required(context.housing_gap, "housing_gap"), 0.0) / max(
        population,
        1.0,
    )
    service_coverage = _service_coverage(context.state)
    context.crime = _crime(
        satisfaction=_required(context.satisfaction, "satisfaction"),
        pollution=_required(context.pollution, "pollution"),
        unemployment_rate=labor_market["unemployment_rate"],
        housing_pressure=housing_pressure,
        service_coverage=service_coverage,
        parameters=context.parameters,
        sensitivity=context.state.sensitivity,
    )
    context.sentiment_signals = _sentiment_signals(
        state=context.state,
        demographics=_required(context.demographics, "demographics"),
        satisfaction=_required(context.satisfaction, "satisfaction"),
        growth_rate=_required(context.growth_rate, "growth_rate"),
        jobs_delta=_required(context.jobs_delta, "jobs_delta"),
        pollution=_required(context.pollution, "pollution"),
        unemployment_rate=labor_market["unemployment_rate"],
        job_vacancy_rate=labor_market["job_vacancy_rate"],
        crime=context.crime,
        housing_pressure=housing_pressure,
        service_coverage=service_coverage,
        parameters=context.parameters,
        sensitivity=context.state.sensitivity,
        signal_ledger=_required(context.signal_ledger, "signal_ledger"),
    )
    context.public_sentiment = _public_sentiment(context.sentiment_signals, context.parameters)


def _step_commit_state(context: AnnualTurnContext) -> None:
    signal_ledger = _required(context.signal_ledger, "signal_ledger")
    context.next_state = CityState(
        year=context.state.year + 1,
        population=_required(context.population, "population"),
        demographics=_required(context.demographics, "demographics"),
        population_profile=context.state.population_profile,
        cohort_profiles=context.state.cohort_profiles,
        physical_profile=context.state.physical_profile,
        civic_assets=context.state.civic_assets,
        neighborhoods=context.state.neighborhoods,
        place_assets=context.state.place_assets,
        people=context.state.people,
        households=context.state.households,
        organizations=context.state.organizations,
        sector_market_balances=context.state.sector_market_balances,
        inventories=context.state.inventories,
        housing_stock=context.state.housing_stock,
        housing_assistance=context.state.housing_assistance,
        housing_units=_required(context.housing_units, "housing_units"),
        jobs=_required(context.jobs, "jobs"),
        budget=_required(context.budget, "budget"),
        annual_income=context.state.annual_income,
        annual_budget=context.state.annual_budget,
        revenue_sources=context.state.revenue_sources,
        infrastructure=_required(context.infrastructure, "infrastructure"),
        pollution=_required(context.pollution, "pollution"),
        satisfaction=_required(context.satisfaction, "satisfaction"),
        metrics=_city_metrics(
            state=context.state,
            population=_required(context.population, "population"),
            demographics=_required(context.demographics, "demographics"),
            jobs=_required(context.jobs, "jobs"),
            jobs_delta=_required(context.jobs_delta, "jobs_delta"),
            housing_units=_required(context.housing_units, "housing_units"),
            housing_gap=_required(context.housing_gap, "housing_gap"),
            satisfaction=_required(context.satisfaction, "satisfaction"),
            infrastructure=_required(context.infrastructure, "infrastructure"),
            pollution=_required(context.pollution, "pollution"),
            growth_rate=_required(context.growth_rate, "growth_rate"),
            parameters=context.parameters,
            sensitivity=context.state.sensitivity,
            signal_ledger=signal_ledger,
            labor_market=_required(context.labor_market, "labor_market"),
            crime=_required(context.crime, "crime"),
            sentiment_signals=_required(context.sentiment_signals, "sentiment_signals"),
            public_sentiment=_required(context.public_sentiment, "public_sentiment"),
        ),
        sensitivity=context.state.sensitivity,
        pending_effects=_advance_delayed_effects(context.state.pending_effects)
        + _delayed_effects_from_signals(signal_ledger),
    )


def _step_detect_issues(context: AnnualTurnContext) -> None:
    context.active_issues = detect_issues(
        _required(context.next_state, "next_state"),
        context.parameters,
        context.signal_ledger,
    )


ANNUAL_TURN_STEPS = (
    TurnStep(
        "validate_inputs",
        _step_validate_inputs,
        produces=("previous_issues",),
    ),
    TurnStep(
        "local_fiscal_policy",
        _step_local_fiscal_policy,
        produces=("revenue", "expenses", "budget"),
    ),
    TurnStep(
        "development_and_jobs",
        _step_development_and_jobs,
        produces=("housing_units", "jobs_delta", "jobs"),
    ),
    TurnStep(
        "infrastructure_environment",
        _step_infrastructure_environment,
        requires=("jobs_delta",),
        produces=("infrastructure", "pollution"),
    ),
    TurnStep(
        "seasonal_signals",
        _step_seasonal_signals,
        requires=("housing_units", "infrastructure", "pollution"),
        produces=("housing_gap", "signal_ledger"),
    ),
    TurnStep(
        "satisfaction_migration_demographics",
        _step_satisfaction_migration_demographics,
        requires=("infrastructure", "pollution", "housing_gap"),
        produces=("satisfaction", "population_delta", "population", "demographics", "growth_rate"),
    ),
    TurnStep(
        "labor_market",
        _step_labor_market,
        requires=("population", "demographics", "jobs", "infrastructure"),
        produces=("labor_market",),
    ),
    TurnStep(
        "sentiment",
        _step_sentiment,
        requires=(
            "jobs_delta",
            "pollution",
            "housing_gap",
            "signal_ledger",
            "satisfaction",
            "population",
            "demographics",
            "growth_rate",
            "labor_market",
        ),
        produces=("crime", "sentiment_signals", "public_sentiment"),
    ),
    TurnStep(
        "commit_state",
        _step_commit_state,
        requires=(
            "budget",
            "housing_units",
            "jobs",
            "jobs_delta",
            "infrastructure",
            "pollution",
            "housing_gap",
            "signal_ledger",
            "satisfaction",
            "population_delta",
            "population",
            "demographics",
            "growth_rate",
            "labor_market",
            "crime",
            "sentiment_signals",
            "public_sentiment",
        ),
        produces=("next_state",),
    ),
    TurnStep(
        "detect_issues",
        _step_detect_issues,
        requires=("next_state", "signal_ledger"),
        produces=("active_issues",),
    ),
)
