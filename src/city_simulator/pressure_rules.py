from __future__ import annotations

from city_simulator.fiscal import deficit_stress
from city_simulator.state import Issue, ModelParameters, SignalLedger


def add_basic_pressure_signals(
    *,
    ledger: SignalLedger,
    housing_gap: float,
    population: float,
    infrastructure: float,
    budget: float,
    expenses: float,
    state_budget_basis: float,
    previous_issues: list[Issue],
    parameters: ModelParameters,
    residential_capacity: float,
) -> None:
    add_housing_pressure_signals(
        ledger=ledger,
        housing_gap=housing_gap,
        population=population,
        parameters=parameters,
        residential_capacity=residential_capacity,
    )
    add_infrastructure_pressure_signals(
        ledger=ledger,
        infrastructure=infrastructure,
        parameters=parameters,
    )
    add_fiscal_pressure_signals(
        ledger=ledger,
        budget=budget,
        expenses=expenses,
        state_budget_basis=state_budget_basis,
        previous_issues=previous_issues,
    )


def add_housing_pressure_signals(
    *,
    ledger: SignalLedger,
    housing_gap: float,
    population: float,
    parameters: ModelParameters,
    residential_capacity: float,
) -> None:
    housing_gap = max(housing_gap, 0.0)
    housing_pressure = housing_gap / max(population, 1.0)
    excess_housing_pressure = max(
        housing_pressure - parameters.housing_pressure_threshold,
        0.0,
    )
    if excess_housing_pressure <= 0:
        return

    pressure_amount = excess_housing_pressure * parameters.housing_build_pressure_multiplier
    ledger.add(
        "housing_growth_pressure",
        pressure_amount,
        "Population demand is outpacing available homes.",
        driver_categories=("resident_household_behavior", "market_forces"),
    )
    if residential_capacity >= housing_gap:
        ledger.add(
            "residential_build_pressure",
            pressure_amount,
            (
                "Residentially zoned capacity can absorb the housing gap if "
                "policy, permitting, and investment allow it."
            ),
            driver_categories=("resident_household_behavior", "market_forces", "policy"),
        )
        return

    constrained_share = (housing_gap - residential_capacity) / max(housing_gap, 1.0)
    constraint_pressure = (
        constrained_share
        * excess_housing_pressure
        * parameters.housing_land_constraint_multiplier
    )
    ledger.add(
        "residential_land_constraint_pressure",
        constraint_pressure,
        (
            "Housing demand exceeds available residential capacity, "
            "creating land-use and displacement pressure."
        ),
        driver_categories=("resident_household_behavior", "market_forces", "policy"),
    )
    ledger.add(
        "business_housing_pressure",
        constraint_pressure * parameters.housing_business_pressure_multiplier / 100,
        "Housing scarcity makes it harder for employers to attract and retain workers.",
        driver_categories=("market_forces", "resident_household_behavior"),
    )
    if constraint_pressure >= 6.0:
        ledger.add(
            "civic_trust_risk",
            constraint_pressure * 0.22,
            "Visible housing scarcity reduces confidence in land-use and growth management.",
            driver_categories=("policy", "resident_household_behavior"),
        )
        ledger.add(
            "future_confidence_risk",
            constraint_pressure * 0.2,
            "Constrained residential capacity lowers confidence in future affordability and growth.",
            driver_categories=("policy", "market_forces"),
        )


def add_infrastructure_pressure_signals(
    *,
    ledger: SignalLedger,
    infrastructure: float,
    parameters: ModelParameters,
) -> None:
    infrastructure_pressure = max(
        parameters.infrastructure_pressure_threshold - infrastructure,
        0.0,
    )
    if infrastructure_pressure > 0:
        ledger.add(
            "infrastructure_decline_pressure",
            infrastructure_pressure,
            "Aging infrastructure creates mounting reliability, access, and repair problems.",
            driver_categories=("baseline_dynamics", "institutional_behavior"),
        )
        ledger.add(
            "resident_infrastructure_burden",
            infrastructure_pressure * parameters.infrastructure_resident_burden_multiplier,
            "Residents face utility interruptions, rougher commutes, safety risk, and daily friction.",
            driver_categories=("baseline_dynamics", "resident_household_behavior"),
        )
        ledger.add(
            "service_disruption_risk",
            infrastructure_pressure * parameters.infrastructure_service_disruption_multiplier,
            "Aging infrastructure makes public and utility services less reliable.",
            driver_categories=("baseline_dynamics", "institutional_behavior"),
        )
        ledger.add(
            "organization_disruption_risk",
            infrastructure_pressure * parameters.infrastructure_organization_disruption_multiplier,
            "Organizations and businesses lose productivity when utilities, roads, and facilities degrade.",
            driver_categories=("baseline_dynamics", "institutional_behavior", "market_forces"),
        )
    if infrastructure_pressure >= 18.0:
        ledger.add(
            "civic_trust_risk",
            infrastructure_pressure * 0.18,
            "Visible infrastructure failures reduce confidence in maintenance and capital planning.",
            driver_categories=("baseline_dynamics", "institutional_behavior"),
        )
        ledger.add(
            "future_confidence_risk",
            infrastructure_pressure * 0.2,
            "Mounting repair needs lower confidence in future services and growth capacity.",
            driver_categories=("baseline_dynamics", "institutional_behavior", "market_forces"),
        )


def add_fiscal_pressure_signals(
    *,
    ledger: SignalLedger,
    budget: float,
    expenses: float,
    state_budget_basis: float,
    previous_issues: list[Issue],
) -> None:
    fiscal_stress = deficit_stress(budget, max(expenses, state_budget_basis))
    persistent_deficit = any(issue.code == "budget_deficit" for issue in previous_issues)
    if fiscal_stress > 0:
        if persistent_deficit:
            fiscal_stress *= 1.2
        ledger.add(
            "fiscal_stress",
            fiscal_stress,
            "Deficit size and persistence create fiscal stress beyond the budget label.",
            driver_categories=("policy", "institutional_behavior"),
        )
    if fiscal_stress >= 8.0:
        ledger.add(
            "civic_trust_risk",
            fiscal_stress * 0.28,
            "Residents and institutions lose confidence when deficits threaten service stability.",
            driver_categories=("policy", "institutional_behavior"),
        )
    if fiscal_stress >= 12.0:
        ledger.add(
            "future_confidence_risk",
            fiscal_stress * 0.35,
            "Large fiscal gaps lower confidence in future services, taxes, and investment capacity.",
            driver_categories=("policy", "institutional_behavior", "market_forces"),
        )
