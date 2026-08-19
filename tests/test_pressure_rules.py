import pytest

from city_simulator import (
    CityMetrics,
    CityPolicy,
    CityState,
    Demographics,
    Neighborhood,
    ZoningEnvelope,
)
from city_simulator.model import advance_year


def test_small_deficit_is_tolerated_without_fiscal_crisis():
    city = CityState(
        population=100_000,
        budget=0,
        annual_income=49_000_000,
        annual_budget=50_000_000,
    )

    result = advance_year(city, CityPolicy())
    issues = {issue.code: issue for issue in result.active_issues}

    assert result.state.budget == pytest.approx(-1_000_000)
    assert result.signal_ledger.get("fiscal_stress") == pytest.approx(2.0)
    assert issues["budget_deficit"].severity == "low"
    assert "fiscal_crisis" not in issues


def test_persistent_large_deficit_hits_trust_confidence_and_crisis():
    city = CityState(
        population=100_000,
        budget=-12_000_000,
        annual_income=42_000_000,
        annual_budget=50_000_000,
        satisfaction=58,
    )

    result = advance_year(city, CityPolicy())
    issues = {issue.code: issue for issue in result.active_issues}

    assert result.signal_ledger.get("fiscal_stress") > 35
    assert result.signal_ledger.get("civic_trust_risk") > 0
    assert result.signal_ledger.get("future_confidence_risk") > 0
    assert issues["budget_deficit"].severity == "high"
    assert issues["fiscal_crisis"].severity == "high"
    assert result.state.metrics.sentiment_signals["civic_trust"] < 55
    assert result.state.metrics.sentiment_signals["future_confidence"] < 45


def test_aging_infrastructure_creates_resident_and_organization_pressure():
    strong = advance_year(
        CityState(infrastructure=78),
        CityPolicy(transit_investment=0, services_investment=0),
    )
    aging = advance_year(
        CityState(infrastructure=43),
        CityPolicy(transit_investment=0, services_investment=0),
    )

    assert aging.signal_ledger.get("infrastructure_decline_pressure") > 0
    assert aging.signal_ledger.get("resident_infrastructure_burden") > 0
    assert aging.signal_ledger.get("service_disruption_risk") > 0
    assert aging.signal_ledger.get("organization_disruption_risk") > 0
    assert aging.signal_ledger.get("civic_trust_risk") > 0
    assert "aging_infrastructure" in {issue.code for issue in aging.active_issues}
    assert aging.state.satisfaction < strong.state.satisfaction
    assert (
        aging.state.metrics.sentiment_signals["business_behavior"]
        < strong.state.metrics.sentiment_signals["business_behavior"]
    )
    assert (
        aging.state.metrics.sentiment_signals["services"]
        < strong.state.metrics.sentiment_signals["services"]
    )


def test_infrastructure_investment_lever_reduces_aging_pressure():
    neglected = advance_year(
        CityState(infrastructure=43),
        CityPolicy(transit_investment=0, services_investment=0),
    )
    maintained = advance_year(
        CityState(infrastructure=43),
        CityPolicy(transit_investment=220_000_000, services_investment=70_000_000),
    )

    assert maintained.state.infrastructure > neglected.state.infrastructure
    assert maintained.signal_ledger.get(
        "infrastructure_decline_pressure"
    ) < neglected.signal_ledger.get("infrastructure_decline_pressure")
    assert maintained.state.satisfaction > neglected.state.satisfaction


def test_housing_growth_pressure_emits_build_signal_when_capacity_exists():
    city = CityState(
        population=120_000,
        housing_units=43_000,
        neighborhoods={
            "station": Neighborhood(
                name="Station",
                population=120_000,
                housing_units=43_000,
                zoning=ZoningEnvelope(
                    allowed_uses=("residential", "mixed_use"),
                    max_housing_units=62_000,
                ),
            )
        },
    )

    result = advance_year(city, CityPolicy(housing_investment=0))

    assert result.signal_ledger.get("housing_growth_pressure") > 0
    assert result.signal_ledger.get("residential_build_pressure") > 0
    assert result.signal_ledger.get("residential_land_constraint_pressure") == 0


def test_housing_growth_pressure_spills_over_when_land_is_constrained():
    constrained = CityState(
        population=120_000,
        housing_units=43_000,
        neighborhoods={
            "built-out": Neighborhood(
                name="Built Out",
                population=120_000,
                housing_units=43_000,
                zoning=ZoningEnvelope(max_housing_units=44_000),
            )
        },
    )
    flexible = CityState(
        population=120_000,
        housing_units=43_000,
        neighborhoods={
            "growth": Neighborhood(
                name="Growth",
                population=120_000,
                housing_units=43_000,
                zoning=ZoningEnvelope(max_housing_units=62_000),
            )
        },
    )

    constrained_result = advance_year(constrained, CityPolicy(housing_investment=0))
    flexible_result = advance_year(flexible, CityPolicy(housing_investment=0))

    assert constrained_result.signal_ledger.get("residential_land_constraint_pressure") > 0
    assert constrained_result.signal_ledger.get("business_housing_pressure") > 0
    assert constrained_result.signal_ledger.get("civic_trust_risk") > 0
    assert (
        constrained_result.state.metrics.sentiment_signals["business_behavior"]
        < flexible_result.state.metrics.sentiment_signals["business_behavior"]
    )


def test_work_pressure_pushes_migration_but_household_buffer_softens_it():
    low_buffer = CityState(
        population=100_000,
        demographics=Demographics(
            children=18_000,
            working_age=62_000,
            seniors=20_000,
            low_income=62_000,
            middle_income=28_000,
            high_income=10_000,
        ),
        jobs=38_000,
        metrics=CityMetrics(unemployment_rate=0.16),
    )
    high_buffer = CityState(
        population=100_000,
        demographics=Demographics(
            children=18_000,
            working_age=62_000,
            seniors=20_000,
            low_income=22_000,
            middle_income=48_000,
            high_income=30_000,
        ),
        jobs=38_000,
        metrics=CityMetrics(unemployment_rate=0.16),
    )

    low_buffer_result = advance_year(low_buffer, CityPolicy(business_support=0))
    high_buffer_result = advance_year(high_buffer, CityPolicy(business_support=0))

    assert low_buffer_result.population_delta < high_buffer_result.population_delta


def test_business_support_lever_reduces_work_pressure_and_improves_growth():
    city = CityState(
        population=100_000,
        jobs=38_000,
        metrics=CityMetrics(unemployment_rate=0.16),
    )

    baseline = advance_year(city, CityPolicy(business_support=0))
    intervention = advance_year(city, CityPolicy(business_support=180_000_000))

    assert intervention.jobs_delta > baseline.jobs_delta
    assert intervention.signal_ledger.get("work_access_pressure") < baseline.signal_ledger.get(
        "work_access_pressure"
    )
    assert intervention.population_delta > baseline.population_delta
