from __future__ import annotations

from city_simulator.derived import _clamp
from city_simulator.state import (
    CityPolicy,
    CitySensitivity,
    CityState,
    Demographics,
    ExternalControls,
    ModelParameters,
    SignalLedger,
)


def validate_policy(policy: CityPolicy) -> None:
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


def housing_units_added(
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


def jobs_delta(
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


def advance_demographics(
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


def satisfaction(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls,
    infrastructure: float,
    pollution: float,
    housing_gap: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
    signal_ledger: SignalLedger | None = None,
) -> float:
    ledger = signal_ledger or SignalLedger()
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
    budget_penalty = (
        parameters.budget_deficit_satisfaction_penalty
        if state.budget < 0
        else 0.0
    ) + ledger.get("fiscal_stress") * parameters.fiscal_stress_satisfaction_penalty
    infrastructure_pressure_penalty = (
        ledger.get("resident_infrastructure_burden")
        + ledger.get("service_disruption_risk") * 0.35
    )
    raw = (
        parameters.base_satisfaction
        + infrastructure * parameters.infrastructure_satisfaction_bonus
        + service_score
        - pollution * parameters.pollution_satisfaction_penalty
    )
    return _clamp(
        raw
        - tax_penalty
        - housing_penalty
        - restriction_penalty
        - budget_penalty
        - infrastructure_pressure_penalty,
        0.0,
        100.0,
    )


def population_delta(
    state: CityState,
    policy: CityPolicy,
    satisfaction: float,
    housing_gap: float,
    jobs_delta: float,
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
    opportunity_bonus = (
        max(jobs_delta, 0.0)
        / max(state.population, 1.0)
        * parameters.job_growth_migration_bonus
    )
    work_drag = work_migration_drag(state, parameters)
    return state.population * (
        growth_rate
        - housing_drag
        + migration_rate
        + opportunity_bonus
        + external.federal_growth_pressure
        - tax_migration_drag
        - restriction_drag
        - work_drag
    )


def work_migration_drag(state: CityState, parameters: ModelParameters) -> float:
    unemployment_excess = max(state.metrics.unemployment_rate - 0.065, 0.0)
    if unemployment_excess <= 0:
        return 0.0
    total_income = max(
        state.demographics.low_income
        + state.demographics.middle_income
        + state.demographics.high_income,
        1.0,
    )
    household_buffer = (
        state.demographics.middle_income * 0.6 + state.demographics.high_income
    ) / total_income
    low_income_exposure = state.demographics.low_income / total_income
    buffer_mitigation = household_buffer * parameters.unemployment_household_buffer
    pressure = unemployment_excess * (1.0 + low_income_exposure - buffer_mitigation)
    return max(pressure, 0.0) * parameters.unemployment_migration_drag


def residential_capacity_available(state: CityState) -> float:
    if not state.neighborhoods:
        return 0.0
    capacity = 0.0
    for neighborhood in state.neighborhoods.values():
        max_units = neighborhood.zoning.max_housing_units
        if max_units <= 0:
            continue
        capacity += max(max_units - neighborhood.housing_units, 0.0)
    return capacity
