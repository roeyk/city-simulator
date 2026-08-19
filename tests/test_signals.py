from dataclasses import replace

import pytest

from city_simulator import (
    CityPolicy,
    CityState,
    Demographics,
    EmbeddedService,
    InventoryState,
    InventoryStatusView,
    LanguageProfile,
    LanguageSkill,
    OrganizationAgent,
    PersonAgent,
    PlaceAsset,
    SectorMarketBalance,
    ServiceLanguage,
    SignalLedger,
    active_delayed_effects,
)
from city_simulator.model import advance_year
from city_simulator.signals import SIGNAL_CONCEPTS


def test_default_city_does_not_create_seasonal_heat_cascade():
    result = advance_year(CityState(), CityPolicy())

    assert result.signal_ledger.signals == {}
    assert "seasonal_heat_cascade" not in {issue.code for issue in result.active_issues}
    assert not result.state.pending_effects


def test_signal_ledger_preserves_numeric_signals_and_records_driver_categories():
    ledger = SignalLedger()

    ledger.add(
        "service_gap",
        2.5,
        "First explanation.",
        driver_categories=("institutional_behavior",),
    )
    ledger.add(
        "service_gap",
        1.5,
        "Second explanation.",
        driver_categories=("institutional_behavior", "resident_household_behavior"),
    )

    assert ledger.get("service_gap") == pytest.approx(4)
    assert ledger.explanations["service_gap"] == (
        "First explanation.",
        "Second explanation.",
    )
    assert ledger.drivers_for("service_gap") == (
        "institutional_behavior",
        "resident_household_behavior",
    )


def test_signal_ledger_records_broad_signal_channels():
    ledger = SignalLedger()

    ledger.add(
        "fresh_food_import_gap",
        12.0,
        "Local fresh-food demand exceeds local supply and committed imports.",
        driver_categories=("supply_chain", "regional_spillover"),
    )

    assert ledger.get("fresh_food_import_gap") == pytest.approx(12)
    assert ledger.drivers_for("fresh_food_import_gap") == (
        "supply_chain",
        "regional_spillover",
    )


def test_signal_concepts_declare_need_inputs_outputs_and_channels():
    concepts = {concept.name: concept for concept in SIGNAL_CONCEPTS}

    language = concepts["language_service_access"]
    sector_market = concepts["sector_market_balance"]
    inventory = concepts["inventory_status"]

    assert language.need
    assert "state.people.language_profile" in language.inputs
    assert language.outputs == ("SignalLedger",)
    assert "interpreter_need" in language.channels
    assert "state.sector_market_balances" in sector_market.inputs
    assert "sector_unmet_demand" in sector_market.channels
    assert "state.inventories" in inventory.inputs
    assert "inventory_stockout_risk" in inventory.channels


def test_inventory_status_view_accounts_for_spoilage_adjusted_days_on_hand():
    view = InventoryStatusView.derive_from_inventories(
        (
            InventoryState(
                holder_type="household",
                holder_id="household-1",
                sector="household",
                good="shelf_stable_food",
                quantity=6,
                daily_use=2,
                reorder_threshold_days=5,
                reserve_target_days=7,
            ),
            InventoryState(
                holder_type="organization",
                holder_id="grocery-1",
                sector="grocery",
                good="fresh_food",
                days_on_hand=2,
                reorder_threshold_days=3,
                reserve_target_days=5,
                storage_type="cold_chain",
                spoilage_risk=0.25,
                stockout_risk=0.7,
            ),
        )
    )

    assert view.inventory_records == pytest.approx(2)
    assert view.low_inventory_records == pytest.approx(2)
    assert view.reserve_gap_days == pytest.approx(7.5)
    assert view.stockout_risk == pytest.approx(1.1)
    assert view.cold_chain_exposure_records == pytest.approx(1)
    assert view.spoilage_risk == pytest.approx(0.25)


def test_inventory_records_emit_turn_signals_without_agent_inventory_fields():
    state = CityState(
        inventories=(
            InventoryState(
                holder_type="household",
                holder_id="household-1",
                sector="household",
                good="shelf_stable_food",
                quantity=6,
                daily_use=2,
                reorder_threshold_days=5,
                reserve_target_days=7,
            ),
            InventoryState(
                holder_type="organization",
                holder_id="grocery-1",
                sector="grocery",
                good="fresh_food",
                days_on_hand=2,
                reorder_threshold_days=3,
                reserve_target_days=5,
                storage_type="cold_chain",
                spoilage_risk=0.25,
                stockout_risk=0.7,
            ),
        )
    )

    result = advance_year(state, CityPolicy())

    assert result.state.inventories == state.inventories
    assert result.signal_ledger.get("inventory_reorder_gap") == pytest.approx(2)
    assert result.signal_ledger.get("inventory_reserve_gap") == pytest.approx(7.5)
    assert result.signal_ledger.get("inventory_stockout_risk") == pytest.approx(1.1)
    assert result.signal_ledger.get("cold_chain_failure_risk") == pytest.approx(1)
    assert result.signal_ledger.get("inventory_spoilage_risk") == pytest.approx(0.25)


def test_sector_market_balance_records_accounting_gaps_as_turn_signals():
    state = CityState(
        sector_market_balances=(
            SectorMarketBalance(
                sector="grocery",
                good_or_service="fresh_food",
                local_demand=1_000,
                local_supply=350,
                imports=400,
                inventory_or_capacity_drawdown=50,
                substitution=100,
                price_pressure=0.12,
                utilization=0.97,
                notes=("regional produce distributor",),
            ),
            SectorMarketBalance(
                sector="medical",
                good_or_service="primary_care_visits",
                local_demand=500,
                local_supply=460,
                imports=20,
                wait_pressure=0.2,
            ),
        )
    )

    result = advance_year(state, CityPolicy())

    assert state.sector_market_balances[0].accounted_supply == pytest.approx(900)
    assert state.sector_market_balances[0].effective_unmet_demand == pytest.approx(100)
    assert result.signal_ledger.get("sector_local_supply_gap") == pytest.approx(690)
    assert result.signal_ledger.get("regional_import_dependency") == pytest.approx(420)
    assert result.signal_ledger.get("sector_unmet_demand") == pytest.approx(120)
    assert result.signal_ledger.get("sector_price_pressure") == pytest.approx(0.12)
    assert result.signal_ledger.get("sector_wait_pressure") == pytest.approx(0.2)
    assert result.signal_ledger.get("sector_capacity_strain") == pytest.approx(97)
    assert result.signal_ledger.drivers_for("regional_import_dependency") == (
        "regional_spillover",
        "supply_chain",
        "market_forces",
    )


def test_language_access_records_turn_signals_without_changing_headlines():
    people = (
        PersonAgent(
            "person-1",
            household_id="household-1",
            age=34,
            income_band="middle",
            weight=10,
            language_profile=LanguageProfile(
                skills=(
                    LanguageSkill("english", spoken_proficiency="professional"),
                    LanguageSkill("spanish", spoken_proficiency="professional"),
                )
            ),
        ),
        PersonAgent(
            "person-2",
            household_id="household-2",
            age=42,
            income_band="low",
            weight=30,
            language_profile=LanguageProfile(
                skills=(LanguageSkill("amharic", spoken_proficiency="native"),),
                interpreter_needed=True,
            ),
        ),
    )
    organizations = (
        OrganizationAgent(
            "org-1",
            organization_type="clinic",
            service_languages=(
                ServiceLanguage("english", service_proficiency="professional"),
                ServiceLanguage("spanish", service_proficiency="professional"),
            ),
        ),
    )
    baseline = advance_year(CityState(people=people), CityPolicy())
    with_service_languages = advance_year(
        CityState(people=people, organizations=organizations),
        CityPolicy(),
    )

    assert baseline.signal_ledger.signals == {}
    assert with_service_languages.signal_ledger.get("language_service_access_gap") == (
        pytest.approx(31.25)
    )
    assert with_service_languages.signal_ledger.get("language_limited_access") == (
        pytest.approx(75)
    )
    assert with_service_languages.signal_ledger.get("interpreter_need") == pytest.approx(75)
    assert with_service_languages.signal_ledger.get("multilingual_bridge_capacity") == (
        pytest.approx(25)
    )
    assert with_service_languages.signal_ledger.drivers_for(
        "language_service_access_gap"
    ) == (
        "resident_household_behavior",
        "institutional_behavior",
    )
    assert with_service_languages.signal_ledger.drivers_for("interpreter_need") == (
        "resident_household_behavior",
        "institutional_behavior",
    )
    assert with_service_languages.state.satisfaction == pytest.approx(
        baseline.state.satisfaction
    )
    assert with_service_languages.jobs_delta == pytest.approx(baseline.jobs_delta)
    assert with_service_languages.state.metrics.public_sentiment == pytest.approx(
        baseline.state.metrics.public_sentiment
    )


def test_heat_grid_health_cascade_records_signals_and_delayed_effects():
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

    assert result.signal_ledger.get("summer_heat_exposure") > 10
    assert result.signal_ledger.get("grid_shortfall") > 5
    assert result.signal_ledger.get("healthcare_surge") > 5
    assert result.signal_ledger.drivers_for("summer_heat_exposure") == (
        "environment_seasonality",
        "baseline_dynamics",
        "delayed_effects",
    )
    assert result.signal_ledger.drivers_for("grid_shortfall") == (
        "environment_seasonality",
        "institutional_behavior",
        "policy",
    )
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
