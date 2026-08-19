from __future__ import annotations

from city_simulator.state import CityPolicy, CityState, ModelParameters


def annual_revenue(state: CityState, policy: CityPolicy) -> float:
    source_total = state.revenue_sources.total
    if source_total > 0:
        default_policy = CityPolicy()
        return (
            source_total
            + resident_tax_base(state) * (policy.tax_rate - default_policy.tax_rate)
            + business_tax_base(state)
            * (policy.business_tax_rate - default_policy.business_tax_rate)
        )
    if state.annual_income > 0:
        default_policy = CityPolicy()
        return (
            state.annual_income
            + resident_tax_base(state) * (policy.tax_rate - default_policy.tax_rate)
            + business_tax_base(state)
            * (policy.business_tax_rate - default_policy.business_tax_rate)
        )
    return (
        resident_tax_base(state) * policy.tax_rate
        + business_tax_base(state) * policy.business_tax_rate
    )


def annual_expenses(
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


def tax_base(state: CityState) -> float:
    return resident_tax_base(state) + business_tax_base(state)


def resident_tax_base(state: CityState) -> float:
    return (
        state.demographics.low_income * 16_000
        + state.demographics.middle_income * 34_000
        + state.demographics.high_income * 72_000
    )


def business_tax_base(state: CityState) -> float:
    return state.jobs * 19_000


def budget_basis(state: CityState, parameters: ModelParameters) -> float:
    return max(
        state.annual_budget,
        state.annual_income,
        state.revenue_sources.total,
        state.population * parameters.resident_service_cost_per_person,
        1.0,
    )


def deficit_stress(budget: float, basis: float) -> float:
    if budget >= 0:
        return 0.0
    return abs(budget) / max(basis, 1.0) * 100


def budget_deficit_severity(deficit_stress: float) -> str:
    if deficit_stress >= 10.0:
        return "high"
    if deficit_stress >= 2.5:
        return "medium"
    return "low"
