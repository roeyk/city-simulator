from __future__ import annotations

from dataclasses import replace

from city_simulator.agents import OrganizationAgent, ServiceLanguage
from city_simulator.person_generator import (
    GeneratedFamilyPopulation,
    SyntheticPopulationRecipe,
    generate_synthetic_population,
)
from city_simulator.starter import starter_city
from city_simulator.state import (
    CityState,
    Demographics,
    InventoryState,
    SectorMarketBalance,
)


def generate_synthetic_city(
    people: int = 30,
    recipe: SyntheticPopulationRecipe | None = None,
) -> CityState:
    if people <= 0:
        raise ValueError("people must be positive")
    population = generate_synthetic_population(people, recipe)
    base = starter_city("balanced", population=float(people))
    return replace(
        base,
        population=float(people),
        demographics=_demographics_from_population(population),
        people=population.people,
        households=population.households,
        organizations=population.organizations + _synthetic_anchor_organizations(),
        sector_market_balances=_synthetic_sector_market_balances(float(people)),
        inventories=_synthetic_inventories(population),
    )


def _demographics_from_population(population: GeneratedFamilyPopulation) -> Demographics:
    people = population.people
    return Demographics(
        children=sum(person.weight for person in people if person.is_child),
        working_age=sum(person.weight for person in people if person.is_working_age),
        seniors=sum(person.weight for person in people if person.is_senior),
        low_income=sum(person.weight for person in people if person.income_band == "low"),
        middle_income=sum(person.weight for person in people if person.income_band == "middle"),
        high_income=sum(person.weight for person in people if person.income_band == "high"),
    )


def _synthetic_anchor_organizations() -> tuple[OrganizationAgent, ...]:
    return (
        OrganizationAgent(
            "grocery-1",
            organization_type="grocery_store",
            sector="grocery",
            neighborhood="market_district",
            staff=18,
            display_name="Market District Grocery",
            customer_types=("residents",),
            service_languages=(
                ServiceLanguage("english", service_proficiency="native", staff_capacity=12),
                ServiceLanguage("spanish", service_proficiency="professional", staff_capacity=4),
            ),
        ),
        OrganizationAgent(
            "restaurant-1",
            organization_type="restaurant",
            sector="food_service",
            neighborhood="market_district",
            staff=12,
            display_name="Market District Diner",
            customer_types=("residents", "visitors"),
        ),
        OrganizationAgent(
            "hospital-1",
            organization_type="hospital",
            sector="medical",
            neighborhood="summer_crescent_boulevard",
            staff=220,
            display_name="Crescent General Hospital",
            customer_types=("residents", "regional_patients"),
            service_languages=(
                ServiceLanguage("english", service_proficiency="native", staff_capacity=90),
                ServiceLanguage(
                    "spanish",
                    service_proficiency="professional",
                    staff_capacity=18,
                    interpreter_capacity=4,
                ),
            ),
        ),
        OrganizationAgent(
            "school-district-1",
            organization_type="school_district",
            sector="education",
            neighborhood="village_hills",
            staff=85,
            display_name="Village Hills Schools",
            customer_types=("children", "households"),
        ),
        OrganizationAgent(
            "warehouse-1",
            organization_type="regional_warehouse",
            sector="logistics",
            neighborhood="market_district",
            staff=40,
            display_name="Market District Warehouse",
            customer_types=("businesses", "institutions"),
        ),
    )


def _synthetic_sector_market_balances(people: float) -> tuple[SectorMarketBalance, ...]:
    return (
        SectorMarketBalance(
            sector="grocery",
            good_or_service="fresh_food",
            local_demand=people * 3.0,
            local_supply=people * 0.9,
            imports=people * 1.4,
            inventory_or_capacity_drawdown=people * 0.25,
            substitution=people * 0.15,
            price_pressure=0.08,
            utilization=0.96,
            notes=("synthetic fresh-food import dependency",),
        ),
        SectorMarketBalance(
            sector="medical",
            good_or_service="primary_care_visits",
            local_demand=people * 0.35,
            local_supply=people * 0.28,
            imports=people * 0.03,
            wait_pressure=0.18,
            utilization=0.91,
            notes=("synthetic medical access pressure",),
        ),
    )


def _synthetic_inventories(population: GeneratedFamilyPopulation) -> tuple[InventoryState, ...]:
    household_inventories = tuple(
        InventoryState(
            holder_type="household",
            holder_id=household.agent_id,
            sector="household",
            good="shelf_stable_food",
            quantity=6 + (index % 4),
            daily_use=max(len(household.member_ids), 1),
            reorder_threshold_days=4,
            reserve_target_days=7,
            notes=("synthetic household pantry",),
        )
        for index, household in enumerate(population.households)
    )
    organization_inventories = (
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
            notes=("synthetic refrigerated inventory",),
        ),
        InventoryState(
            holder_type="organization",
            holder_id="restaurant-1",
            sector="food_service",
            good="fresh_food",
            days_on_hand=1.5,
            reorder_threshold_days=2,
            reserve_target_days=4,
            storage_type="refrigerated",
            spoilage_risk=0.2,
            notes=("synthetic restaurant ingredient inventory",),
        ),
        InventoryState(
            holder_type="organization",
            holder_id="hospital-1",
            sector="medical",
            good="medicine",
            days_on_hand=8,
            reorder_threshold_days=10,
            reserve_target_days=14,
            stockout_risk=0.15,
            notes=("synthetic hospital medicine reserve",),
        ),
        InventoryState(
            holder_type="organization",
            holder_id="school-district-1",
            sector="education",
            good="prepared_meals",
            days_on_hand=3,
            reorder_threshold_days=4,
            reserve_target_days=6,
            storage_type="refrigerated",
            spoilage_risk=0.1,
            notes=("synthetic school meal inventory",),
        ),
    )
    return household_inventories + organization_inventories
