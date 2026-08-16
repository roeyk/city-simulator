from dataclasses import replace

import pytest

from city_simulator import (
    CityPolicy,
    CityState,
    DelayedEffect,
    Demographics,
    EmbeddedService,
    PlaceAsset,
    active_delayed_effects,
    simulate,
)
from city_simulator.model import (
    ANNUAL_TURN_STEPS,
    CitySensitivity,
    ModelParameters,
    advance_year,
    detect_issues,
)


def test_simulation_advances_requested_years():
    results = simulate(CityState(), CityPolicy(), 3)

    assert [result.year for result in results] == [1, 2, 3]
    assert results[-1].state.year == 3


def test_annual_turn_steps_are_named_in_dependency_order():
    assert [step.name for step in ANNUAL_TURN_STEPS] == [
        "validate_inputs",
        "local_fiscal_policy",
        "development_and_jobs",
        "infrastructure_environment",
        "seasonal_pressures",
        "satisfaction_migration_demographics",
        "commit_state",
        "detect_issues",
    ]
    produced: set[str] = set()
    for step in ANNUAL_TURN_STEPS:
        assert set(step.requires) <= produced
        produced.update(step.produces)

    assert "next_state" in produced
    assert "active_issues" in produced


def test_default_policy_grows_population_and_jobs():
    result = advance_year(CityState(), CityPolicy())

    assert result.state.population > 100_000
    assert result.state.jobs > 58_000
    assert result.revenue > result.expenses
    assert result.state.demographics.total == pytest.approx(result.state.population)
    assert result.state.metrics.happiness == pytest.approx(result.state.satisfaction)
    assert set(result.state.metrics.sentiment_signals) == {
        "survey",
        "migration_behavior",
        "business_behavior",
        "consumer_spending",
        "savings_security",
        "housing_stress",
        "safety",
        "services",
        "civic_trust",
        "future_confidence",
    }
    assert result.state.metrics.labor_force > 0
    assert result.state.metrics.employed_residents > 0
    assert result.state.metrics.jobs_in_city == pytest.approx(result.state.jobs)
    assert result.state.metrics.unemployment_rate == pytest.approx(
        result.state.metrics.unemployed_residents / result.state.metrics.labor_force
    )
    assert 0 <= result.state.metrics.crime <= 100
    assert 0 <= result.state.metrics.public_sentiment <= 100


def test_housing_investment_reduces_housing_pressure():
    low = advance_year(CityState(), CityPolicy(housing_investment=0))
    high = advance_year(CityState(), CityPolicy(housing_investment=60_000_000))

    assert high.housing_gap < low.housing_gap


def test_invalid_policy_is_rejected():
    with pytest.raises(ValueError, match="tax_rate"):
        simulate(CityState(), CityPolicy(tax_rate=1.4), 1)

    with pytest.raises(ValueError, match="non-negative"):
        simulate(CityState(), CityPolicy(services_investment=-1), 1)

    with pytest.raises(ValueError, match="zoning_restrictiveness"):
        simulate(CityState(), CityPolicy(zoning_restrictiveness=1.2), 1)


def test_negative_year_count_is_rejected():
    with pytest.raises(ValueError, match="years"):
        simulate(CityState(), CityPolicy(), -1)


def test_issues_are_detected_and_overcome():
    stressed = CityState(
        population=100_000,
        housing_units=35_000,
        jobs=44_000,
        budget=-1_000_000,
        infrastructure=48,
        pollution=65,
        satisfaction=40,
    )

    issues = detect_issues(stressed)
    assert {issue.code for issue in issues} >= {
        "housing_shortage",
        "unemployment",
        "budget_deficit",
        "aging_infrastructure",
        "pollution",
        "low_satisfaction",
    }

    result = advance_year(
        stressed,
        CityPolicy(
            tax_rate=0.28,
            housing_investment=300_000_000,
            transit_investment=100_000_000,
            services_investment=180_000_000,
            environment_investment=120_000_000,
            business_support=160_000_000,
        ),
    )

    assert result.overcome_issues
    assert "pollution" in {issue.code for issue in result.overcome_issues}


def test_labor_market_can_have_unemployment_and_vacancies():
    mismatched = CityState(
        population=100_000,
        demographics=CityState().demographics,
        population_profile={
            "education_percent": {
                "less_than_high_school": 38,
                "high_school": 34,
                "some_college": 16,
                "bachelors": 8,
                "graduate": 4,
            }
        },
        jobs=52_000,
        infrastructure=42,
    )

    result = advance_year(mismatched, CityPolicy(business_support=0, transit_investment=0))
    metrics = result.state.metrics

    assert metrics.unemployed_residents > 0
    assert metrics.job_vacancies > 0
    assert metrics.commuters_in > 0
    assert metrics.unemployment_rate > 0.08
    assert "unemployment" in {issue.code for issue in result.active_issues}


def test_turn_preserves_profiles_that_feed_derived_metrics():
    city = CityState(
        population_profile={"education_percent": {"less_than_high_school": 20, "graduate": 15}},
        cohort_profiles={"age_income_percent": {"under_18": {"low": 60, "middle": 35, "high": 5}}},
        physical_profile={"area_square_miles": 50},
        civic_assets={"schools": 40, "fire_stations": 10, "police_stations": 6, "libraries": 8},
        place_assets=(
            PlaceAsset(
                name="Public Works Depot",
                asset_type="public_works_depot",
                services=(
                    EmbeddedService(
                        name="Street Cleaning",
                        service_type="street_cleaning",
                        capacity=25,
                    ),
                ),
            ),
        ),
        pending_effects=(
            DelayedEffect(
                source="summer_blackout",
                target="civic_trust",
                amount=-4.0,
                duration_turns=2,
                decay_rate=0.25,
            ),
        ),
    )

    result = advance_year(city, CityPolicy())

    assert result.state.population_profile == city.population_profile
    assert result.state.cohort_profiles == city.cohort_profiles
    assert result.state.physical_profile == city.physical_profile
    assert result.state.civic_assets == city.civic_assets
    assert result.state.place_assets == city.place_assets
    assert result.state.pending_effects[0].amount == pytest.approx(-3.0)
    assert result.state.metrics.density_per_square_mile > 0


def test_delayed_effects_advance_across_turns():
    city = CityState(
        pending_effects=(
            DelayedEffect(
                source="summer_blackout",
                target="infrastructure_backlog",
                amount=12_000_000,
                delay_turns=1,
                duration_turns=3,
                tags=("grid", "capital_repair"),
            ),
            DelayedEffect(
                source="heat_deaths",
                target="civic_trust",
                amount=-6.0,
                delay_turns=0,
                duration_turns=2,
                decay_rate=0.5,
            ),
        )
    )

    assert [effect.target for effect in active_delayed_effects(city)] == ["civic_trust"]

    after_one = advance_year(city, CityPolicy()).state

    assert [effect.target for effect in active_delayed_effects(after_one)] == [
        "infrastructure_backlog",
        "civic_trust",
    ]
    assert after_one.pending_effects[0].delay_turns == 0
    assert after_one.pending_effects[0].duration_turns == 3
    assert after_one.pending_effects[1].amount == pytest.approx(-3.0)
    assert after_one.pending_effects[1].duration_turns == 1
    assert active_delayed_effects(after_one, "civic_trust")[0].source == "heat_deaths"

    after_two = advance_year(after_one, CityPolicy()).state

    assert [effect.target for effect in after_two.pending_effects] == ["infrastructure_backlog"]
    assert after_two.pending_effects[0].duration_turns == 2


def test_default_city_does_not_create_seasonal_heat_cascade():
    result = advance_year(CityState(), CityPolicy())

    assert result.pressure_ledger.signals == {}
    assert "seasonal_heat_cascade" not in {issue.code for issue in result.active_issues}
    assert not result.state.pending_effects


def test_heat_grid_health_cascade_records_pressures_and_delayed_effects():
    stressed = CityState(
        population=120_000,
        demographics=Demographics(
            children=18_000,
            working_age=72_000,
            seniors=30_000,
            low_income=48_000,
            middle_income=54_000,
            high_income=18_000,
        ),
        physical_profile={
            "area_square_miles": 24,
            "seasonal_exposure": {"summer_heat": 8},
        },
        civic_assets={"schools": 20, "fire_stations": 4, "police_stations": 3, "libraries": 3},
        infrastructure=34,
        pollution=78,
        satisfaction=44,
        place_assets=(
            PlaceAsset(
                name="Old Substation",
                asset_type="electric_substation",
                services=(
                    EmbeddedService(
                        name="Grid Capacity",
                        service_type="electric_grid",
                        capacity=20,
                    ),
                ),
            ),
            PlaceAsset(
                name="Neighborhood Clinic",
                asset_type="clinic",
                services=(
                    EmbeddedService(
                        name="Urgent Care",
                        service_type="healthcare",
                        capacity=12,
                    ),
                ),
            ),
        ),
    )

    result = advance_year(
        stressed,
        CityPolicy(environment_investment=0, transit_investment=0, services_investment=0),
    )

    assert result.pressure_ledger.get("summer_heat_exposure") > 10
    assert result.pressure_ledger.get("grid_shortfall") > 5
    assert result.pressure_ledger.get("healthcare_surge") > 5
    assert "seasonal_heat_cascade" in {issue.code for issue in result.active_issues}
    assert {
        effect.target for effect in result.state.pending_effects
    } >= {
        "infrastructure_backlog",
        "healthcare_surge",
        "civic_trust",
    }

    after_one = advance_year(result.state, CityPolicy()).state
    without_trust_effect = replace(
        result.state,
        pending_effects=tuple(
            effect for effect in result.state.pending_effects if effect.target != "civic_trust"
        ),
    )
    after_one_without_trust_effect = advance_year(without_trust_effect, CityPolicy()).state
    after_two = advance_year(after_one, CityPolicy()).state
    after_two_without_trust_effect = advance_year(
        after_one_without_trust_effect,
        CityPolicy(),
    ).state

    assert active_delayed_effects(after_one, "civic_trust")
    assert (
        after_two.metrics.sentiment_signals["civic_trust"]
        < after_two_without_trust_effect.metrics.sentiment_signals["civic_trust"]
    )


def test_model_parameters_change_turn_behavior_without_rewriting_formulas():
    baseline = advance_year(CityState(), CityPolicy())
    expensive_services = advance_year(
        CityState(),
        CityPolicy(),
        parameters=ModelParameters(resident_service_cost_per_person=700),
    )

    assert expensive_services.expenses > baseline.expenses
    assert expensive_services.state.budget < baseline.state.budget


def test_city_sensitivity_changes_derived_metrics():
    fragile = CityState(
        jobs=38_000,
        infrastructure=45,
        sensitivity=CitySensitivity(
            crime_unemployment=1.8,
            sentiment_financial_stress=1.4,
        )
    )
    resilient = CityState(
        jobs=38_000,
        infrastructure=45,
        sensitivity=CitySensitivity(
            crime_unemployment=0.6,
            sentiment_financial_stress=0.7,
        )
    )

    fragile_result = advance_year(fragile, CityPolicy(business_support=0))
    resilient_result = advance_year(resilient, CityPolicy(business_support=0))

    assert fragile_result.state.metrics.crime > resilient_result.state.metrics.crime
    assert (
        fragile_result.state.metrics.sentiment_signals["savings_security"]
        < resilient_result.state.metrics.sentiment_signals["savings_security"]
    )


def test_migration_and_restrictions_change_population():
    welcoming = simulate(
        CityState(),
        CityPolicy(
            citizen_influx_rate=0.02,
            citizen_outflux_rate=0.001,
            zoning_restrictiveness=0.1,
            permitting_speed=0.9,
            development_restriction=0.05,
        ),
        5,
    )[-1]
    restrictive = simulate(
        CityState(),
        CityPolicy(
            citizen_influx_rate=0.002,
            citizen_outflux_rate=0.012,
            zoning_restrictiveness=0.9,
            permitting_speed=0.1,
            development_restriction=0.85,
        ),
        5,
    )[-1]

    assert welcoming.state.population > restrictive.state.population
    assert welcoming.state.housing_units > restrictive.state.housing_units
