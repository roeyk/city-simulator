from __future__ import annotations

from typing import TypeVar

from city_simulator.annual_dynamics import (
    advance_demographics,
    housing_units_added,
    jobs_delta,
    population_delta,
    residential_capacity_available,
    satisfaction,
    validate_policy,
)
from city_simulator.derived import _clamp, _service_coverage
from city_simulator.fiscal import annual_expenses, annual_revenue, budget_basis
from city_simulator.issues import detect_issues
from city_simulator.metrics import (
    _city_metrics,
    _crime,
    _labor_market,
    _public_sentiment,
    _sentiment_signals,
)
from city_simulator.pressure_rules import add_basic_pressure_signals
from city_simulator.signals import (
    SignalContext,
    _delayed_effects_from_signals,
    signal_ledger_for_turn,
)
from city_simulator.state import (
    CityPolicy,
    CityState,
    DelayedEffect,
    ExternalControls,
    Issue,
    ModelParameters,
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


def _advance_delayed_effects(effects: tuple[DelayedEffect, ...]) -> tuple[DelayedEffect, ...]:
    advanced: list[DelayedEffect] = []
    for effect in effects:
        next_effect = effect.advance()
        if next_effect is not None:
            advanced.append(next_effect)
    return tuple(advanced)



def _overcome_issues(previous: list[Issue], current: list[Issue]) -> list[Issue]:
    current_codes = {issue.code for issue in current}
    return [issue for issue in previous if issue.code not in current_codes]


def _required(value: T | None, name: str) -> T:
    if value is None:
        raise RuntimeError(f"annual turn step did not produce {name}")
    return value


def _step_validate_inputs(context: AnnualTurnContext) -> None:
    validate_policy(context.policy)
    context.previous_issues = detect_issues(context.state, context.parameters)


def _step_local_fiscal_policy(context: AnnualTurnContext) -> None:
    intergovernmental_funding = (
        context.external.county_funding
        + context.external.state_funding
        + context.external.federal_funding
    )
    context.revenue = annual_revenue(context.state, context.policy) + intergovernmental_funding
    financing_cost = (
        max(context.state.budget, 0.0)
        * max(context.external.national_interest_rate, 0.0)
        * context.parameters.financing_cost_budget_share
    )
    context.expenses = annual_expenses(context.state, context.policy, context.parameters) + financing_cost
    context.budget = context.state.budget + context.revenue - context.expenses


def _step_development_and_jobs(context: AnnualTurnContext) -> None:
    context.housing_units = context.state.housing_units + housing_units_added(
        context.policy,
        context.external,
        context.parameters,
        context.state.sensitivity,
    )
    context.jobs_delta = jobs_delta(
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


def _step_basic_pressure_signals(context: AnnualTurnContext) -> None:
    add_basic_pressure_signals(
        ledger=_required(context.signal_ledger, "signal_ledger"),
        housing_gap=_required(context.housing_gap, "housing_gap"),
        population=context.state.population,
        infrastructure=_required(context.infrastructure, "infrastructure"),
        budget=_required(context.budget, "budget"),
        expenses=_required(context.expenses, "expenses"),
        state_budget_basis=budget_basis(context.state, context.parameters),
        previous_issues=context.previous_issues,
        parameters=context.parameters,
        residential_capacity=residential_capacity_available(context.state),
    )


def _step_satisfaction_migration_demographics(context: AnnualTurnContext) -> None:
    context.satisfaction = satisfaction(
        context.state,
        context.policy,
        context.external,
        _required(context.infrastructure, "infrastructure"),
        _required(context.pollution, "pollution"),
        _required(context.housing_gap, "housing_gap"),
        context.parameters,
        context.state.sensitivity,
        _required(context.signal_ledger, "signal_ledger"),
    )
    context.population_delta = population_delta(
        context.state,
        context.policy,
        context.satisfaction,
        _required(context.housing_gap, "housing_gap"),
        _required(context.jobs_delta, "jobs_delta"),
        context.external,
        context.parameters,
    )
    context.population = max(0.0, context.state.population + context.population_delta)
    context.demographics = advance_demographics(
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
    unemployment_rate = context.labor_market["unemployment_rate"]
    unemployment_excess = max(unemployment_rate - 0.065, 0.0)
    context.work_pressure = unemployment_excess * 100
    if context.work_pressure > 0:
        _required(context.signal_ledger, "signal_ledger").add(
            "work_access_pressure",
            context.work_pressure,
            (
                "Residents who cannot find suitable work are more likely to leave "
                "or lose trust in government response."
            ),
            driver_categories=(
                "resident_household_behavior",
                "market_forces",
                "institutional_behavior",
            ),
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
        parcel_grid=context.state.parcel_grid,
        parcels=context.state.parcels,
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
        "basic_pressure_signals",
        _step_basic_pressure_signals,
        requires=("budget", "expenses", "signal_ledger"),
        produces=("signal_ledger",),
    ),
    TurnStep(
        "satisfaction_migration_demographics",
        _step_satisfaction_migration_demographics,
        requires=("infrastructure", "pollution", "housing_gap", "signal_ledger"),
        produces=("satisfaction", "population_delta", "population", "demographics", "growth_rate"),
    ),
    TurnStep(
        "labor_market",
        _step_labor_market,
        requires=("population", "demographics", "jobs", "infrastructure", "signal_ledger"),
        produces=("labor_market", "work_pressure", "signal_ledger"),
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
