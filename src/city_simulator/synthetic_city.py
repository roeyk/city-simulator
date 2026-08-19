from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from city_simulator.agents import OrganizationAgent, ServiceLanguage
from city_simulator.person_generator import (
    FamilyGenerationSpec,
    GeneratedFamilyPopulation,
    SyntheticPopulationRecipe,
    enrich_synthetic_population,
    generate_family_population,
    generate_synthetic_population,
)
from city_simulator.starter import starter_city
from city_simulator.state import (
    CityState,
    Demographics,
    InventoryState,
    SectorMarketBalance,
)


@dataclass(frozen=True)
class SyntheticGroupProfile:
    heritage: str
    population_share: float
    income_bands: tuple[tuple[str, float], ...] = ()
    job_pools: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class SyntheticHouseholdMemberProfile:
    heritage: str
    income_band: str
    age: int | None = None


@dataclass(frozen=True)
class SyntheticMixedHouseholdProfile:
    members: tuple[SyntheticHouseholdMemberProfile, ...]
    count: int = 1
    job_pools: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class SyntheticPopulationProfile:
    groups: tuple[SyntheticGroupProfile, ...]
    mixed_households: tuple[SyntheticMixedHouseholdProfile, ...] = ()


def generate_synthetic_city(
    people: int = 30,
    recipe: SyntheticPopulationRecipe | None = None,
    group_profiles: tuple[SyntheticGroupProfile, ...] = (),
    mixed_households: tuple[SyntheticMixedHouseholdProfile, ...] = (),
) -> CityState:
    if people <= 0:
        raise ValueError("people must be positive")
    population = (
        generate_grouped_synthetic_population(people, group_profiles, recipe, mixed_households)
        if group_profiles or mixed_households
        else generate_synthetic_population(people, recipe)
    )
    population = enrich_synthetic_population(population)
    base = starter_city("balanced", population=float(people))
    return replace(
        base,
        population=float(people),
        demographics=_demographics_from_population(population),
        people=population.people,
        households=population.households,
        organizations=_merge_organizations(
            population.organizations,
            _synthetic_anchor_organizations(),
        ),
        sector_market_balances=_synthetic_sector_market_balances(float(people)),
        inventories=_synthetic_inventories(population),
    )


def generate_grouped_synthetic_population(
    count: int,
    group_profiles: tuple[SyntheticGroupProfile, ...],
    recipe: SyntheticPopulationRecipe | None = None,
    mixed_households: tuple[SyntheticMixedHouseholdProfile, ...] = (),
) -> GeneratedFamilyPopulation:
    if count < 0:
        raise ValueError("count must be non-negative")
    if not group_profiles and not mixed_households:
        raise ValueError("group_profiles or mixed_households must not be empty")
    if recipe is None:
        recipe = SyntheticPopulationRecipe()
    if group_profiles:
        _validate_group_profiles(group_profiles)
    _validate_mixed_households(mixed_households)
    specs: list[FamilyGenerationSpec] = []
    household_index = 0
    for mixed_profile in mixed_households:
        for _ in range(mixed_profile.count):
            specs.append(_mixed_household_spec(mixed_profile, recipe, household_index))
            household_index += 1
    remaining_count = count - sum(
        len(mixed_profile.members) * mixed_profile.count for mixed_profile in mixed_households
    )
    if remaining_count < 0:
        raise ValueError("mixed household members exceed requested people count")
    target_counts = _group_target_counts(remaining_count, group_profiles) if group_profiles else ()
    for group, target_count in zip(group_profiles, target_counts, strict=True):
        remaining = target_count
        group_household_index = 0
        while remaining > 0:
            adults, children = _household_shape(recipe, group_household_index, remaining)
            income_band = _weighted_label(
                group.income_bands or recipe.income_bands,
                group_household_index * 2,
            )
            neighborhood, housing_cost_band = _weighted_neighborhood(
                recipe.neighborhoods,
                household_index,
            )
            adult_ages = tuple(24 + ((household_index + index) * 7 % 42) for index in range(adults))
            specs.append(
                FamilyGenerationSpec(
                    group.heritage,
                    household_index=household_index,
                    adults=adults,
                    children=children,
                    income_band=income_band,
                    neighborhood=neighborhood,
                    housing_cost_band=housing_cost_band,
                    job_pools=tuple(
                        _weighted_label(
                            group.job_pools or recipe.job_pools,
                            group_household_index + index,
                        )
                        for index in range(adults)
                    ),
                    adult_income_bands=tuple(
                        _weighted_label(group.income_bands, group_household_index + index)
                        for index in range(adults)
                    )
                    if len(group.income_bands) > 1 and adults > 1
                    else (),
                    adult_ages=adult_ages,
                    adult_education=tuple(
                        _synthetic_education(income_band, group_household_index + index)
                        for index in range(adults)
                    ),
                    adult_experience_years=tuple(max(age - 22, 1) for age in adult_ages),
                    preserve_income_band=bool(group.income_bands),
                )
            )
            remaining -= adults + children
            household_index += 1
            group_household_index += 1
    population = generate_family_population(tuple(specs))
    return GeneratedFamilyPopulation(
        families=population.families,
        households=population.households,
        people=population.people,
        organizations=population.organizations,
    )


def synthetic_group_profiles_from_mapping(data: dict[str, Any]) -> tuple[SyntheticGroupProfile, ...]:
    groups = data.get("groups", ())
    if not isinstance(groups, list | tuple):
        raise TypeError("synthetic profile groups must be an array")
    profiles: list[SyntheticGroupProfile] = []
    for index, value in enumerate(groups):
        if not isinstance(value, dict):
            raise TypeError(f"synthetic profile groups[{index}] must be an object")
        heritage = str(value.get("heritage") or value.get("ethnicity") or "")
        if not heritage:
            raise ValueError(f"synthetic profile groups[{index}] heritage is required")
        share = value.get("population_share", value.get("percent"))
        if not isinstance(share, int | float):
            raise TypeError(f"synthetic profile groups[{index}] population_share is required")
        profiles.append(
            SyntheticGroupProfile(
                heritage=heritage,
                population_share=float(share),
                income_bands=_weighted_items_from_mapping(
                    value.get("income_bands", ()),
                    f"synthetic profile groups[{index}].income_bands",
                ),
                job_pools=_weighted_items_from_mapping(
                    value.get("job_pools", value.get("vocations", ())),
                    f"synthetic profile groups[{index}].job_pools",
                ),
            )
        )
    return tuple(profiles)


def synthetic_population_profile_from_mapping(data: dict[str, Any]) -> SyntheticPopulationProfile:
    return SyntheticPopulationProfile(
        groups=synthetic_group_profiles_from_mapping(data),
        mixed_households=_mixed_household_profiles_from_mapping(data),
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


def _merge_organizations(
    primary: tuple[OrganizationAgent, ...],
    overlays: tuple[OrganizationAgent, ...],
) -> tuple[OrganizationAgent, ...]:
    merged = {organization.agent_id: organization for organization in primary}
    order = [organization.agent_id for organization in primary]
    for overlay in overlays:
        existing = merged.get(overlay.agent_id)
        if existing is None:
            merged[overlay.agent_id] = overlay
            order.append(overlay.agent_id)
            continue
        merged[overlay.agent_id] = replace(
            overlay,
            owner_ids=tuple(dict.fromkeys(existing.owner_ids + overlay.owner_ids)),
            employee_ids=tuple(dict.fromkeys(existing.employee_ids + overlay.employee_ids)),
            staff=max(existing.staff, overlay.staff),
            notes=tuple(dict.fromkeys(existing.notes + overlay.notes)),
        )
    return tuple(merged[agent_id] for agent_id in order)


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


def _validate_group_profiles(group_profiles: tuple[SyntheticGroupProfile, ...]) -> None:
    total_share = sum(group.population_share for group in group_profiles)
    if total_share <= 0:
        raise ValueError("group population shares must have positive total weight")
    for group in group_profiles:
        if not group.heritage:
            raise ValueError("group heritage must not be empty")
        if group.population_share < 0:
            raise ValueError("group population shares must be non-negative")
        _validate_weighted_items(group.income_bands, "group income_bands")
        _validate_weighted_items(group.job_pools, "group job_pools")


def _validate_mixed_households(
    mixed_households: tuple[SyntheticMixedHouseholdProfile, ...],
) -> None:
    for index, mixed_household in enumerate(mixed_households):
        if mixed_household.count <= 0:
            raise ValueError(f"mixed_households[{index}].count must be positive")
        if not mixed_household.members:
            raise ValueError(f"mixed_households[{index}].members must not be empty")
        _validate_weighted_items(
            mixed_household.job_pools,
            f"mixed_households[{index}].job_pools",
        )
        for member_index, member in enumerate(mixed_household.members):
            if not member.heritage:
                raise ValueError(
                    f"mixed_households[{index}].members[{member_index}].heritage is required"
                )
            if member.income_band not in {"low", "middle", "high"}:
                raise ValueError(
                    f"mixed_households[{index}].members[{member_index}].income_band "
                    "must be one of: high, low, middle"
                )


def _mixed_household_spec(
    mixed_household: SyntheticMixedHouseholdProfile,
    recipe: SyntheticPopulationRecipe,
    household_index: int,
) -> FamilyGenerationSpec:
    adult_members = tuple(
        member for member in mixed_household.members if member.age is None or member.age >= 18
    )
    child_members = tuple(
        member for member in mixed_household.members if member.age is not None and member.age < 18
    )
    members = adult_members + child_members
    if not adult_members:
        raise ValueError("mixed households must include at least one adult")
    income_band = _household_income_band(tuple(member.income_band for member in members))
    neighborhood, housing_cost_band = _weighted_neighborhood(recipe.neighborhoods, household_index)
    adult_ages = tuple(
        member.age if member.age is not None else 30 + ((household_index + index) % 35)
        for index, member in enumerate(adult_members)
    )
    adult_income_bands = tuple(member.income_band for member in adult_members)
    return FamilyGenerationSpec(
        members[0].heritage,
        member_heritages=tuple(member.heritage for member in members),
        member_income_bands=tuple(member.income_band for member in members),
        member_ages=tuple(member.age for member in members),
        household_index=household_index,
        adults=len(adult_members),
        children=len(child_members),
        income_band=income_band,
        neighborhood=neighborhood,
        housing_cost_band=housing_cost_band,
        job_pools=tuple(
            _weighted_label(mixed_household.job_pools or recipe.job_pools, household_index + index)
            for index in range(len(adult_members))
        ),
        adult_income_bands=adult_income_bands,
        adult_ages=adult_ages,
        adult_education=tuple(
            _synthetic_education(member.income_band, household_index + index)
            for index, member in enumerate(adult_members)
        ),
        adult_experience_years=tuple(max(age - 22, 1) for age in adult_ages),
        preserve_income_band=True,
    )


def _household_income_band(member_income_bands: tuple[str, ...]) -> str:
    if "high" in member_income_bands and "low" not in member_income_bands:
        return "high"
    if "middle" in member_income_bands or {"low", "high"} <= set(member_income_bands):
        return "middle"
    return "low"


def _mixed_household_profiles_from_mapping(
    data: dict[str, Any],
) -> tuple[SyntheticMixedHouseholdProfile, ...]:
    values = data.get("mixed_households", ())
    if not isinstance(values, list | tuple):
        raise TypeError("synthetic profile mixed_households must be an array")
    profiles: list[SyntheticMixedHouseholdProfile] = []
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise TypeError(f"synthetic profile mixed_households[{index}] must be an object")
        members_value = value.get("members")
        if not isinstance(members_value, list | tuple):
            raise TypeError(f"synthetic profile mixed_households[{index}].members must be an array")
        count = value.get("count", 1)
        if not isinstance(count, int):
            raise TypeError(f"synthetic profile mixed_households[{index}].count must be an integer")
        profiles.append(
            SyntheticMixedHouseholdProfile(
                members=tuple(
                    _mixed_household_member_from_mapping(
                        member,
                        f"synthetic profile mixed_households[{index}].members[{member_index}]",
                    )
                    for member_index, member in enumerate(members_value)
                ),
                count=count,
                job_pools=_weighted_items_from_mapping(
                    value.get("job_pools", value.get("vocations", ())),
                    f"synthetic profile mixed_households[{index}].job_pools",
                ),
            )
        )
    _validate_mixed_households(tuple(profiles))
    return tuple(profiles)


def _mixed_household_member_from_mapping(
    value: Any,
    label: str,
) -> SyntheticHouseholdMemberProfile:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    heritage = str(value.get("heritage") or value.get("ethnicity") or "")
    income_band = str(value.get("income_band") or value.get("class") or "")
    age_value = value.get("age")
    if not heritage:
        raise ValueError(f"{label}.heritage is required")
    if not income_band:
        raise ValueError(f"{label}.income_band is required")
    if age_value is not None and not isinstance(age_value, int):
        raise TypeError(f"{label}.age must be an integer")
    return SyntheticHouseholdMemberProfile(heritage=heritage, income_band=income_band, age=age_value)


def _group_target_counts(
    count: int,
    group_profiles: tuple[SyntheticGroupProfile, ...],
) -> tuple[int, ...]:
    total_share = sum(group.population_share for group in group_profiles)
    allocated = 0
    targets: list[int] = []
    for group in group_profiles[:-1]:
        target = round(count * group.population_share / total_share)
        targets.append(target)
        allocated += target
    targets.append(count - allocated)
    return tuple(targets)


def _household_shape(
    recipe: SyntheticPopulationRecipe,
    household_index: int,
    remaining: int,
) -> tuple[int, int]:
    if remaining <= 1:
        return (1, 0)
    fitting_shapes = tuple(
        (adults, children, weight)
        for adults, children, weight in recipe.household_shapes
        if adults + children <= remaining
    )
    if not fitting_shapes:
        return (1, 0)
    adults, children, _weight = _weighted_item(fitting_shapes, household_index)
    return (adults, children)


def _synthetic_education(income_band: str, index: int) -> str:
    match income_band:
        case "high":
            choices = (("college", 60.0), ("graduate", 40.0))
        case "middle":
            choices = (("high_school", 35.0), ("trade", 30.0), ("college", 35.0))
        case _:
            choices = (("high_school", 70.0), ("trade", 25.0), ("college", 5.0))
    return _weighted_label(choices, index)


def _weighted_neighborhood(
    values: tuple[tuple[str, str, float], ...],
    index: int,
) -> tuple[str, str]:
    neighborhood, housing_cost_band, _weight = _weighted_item(values, index)
    return (neighborhood, housing_cost_band)


def _weighted_label(values: tuple[tuple[str, float], ...], index: int) -> str:
    label, _weight = _weighted_item(values, index)
    return label


def _weighted_item(values: tuple[Any, ...], index: int) -> Any:
    total = sum(value[-1] for value in values)
    if total <= 0:
        raise ValueError("weighted choices must have positive total weight")
    target = (index * 37) % round(total)
    cumulative = 0
    for value in values:
        cumulative += round(value[-1])
        if target < cumulative:
            return value
    return values[-1]


def _weighted_items_from_mapping(value: Any, label: str) -> tuple[tuple[str, float], ...]:
    if value in (None, (), {}):
        return ()
    if isinstance(value, dict):
        items = tuple((str(item_label), float(weight)) for item_label, weight in value.items())
    elif isinstance(value, list | tuple):
        items = tuple(_weighted_pair_from_value(item, f"{label}[]") for item in value)
    else:
        raise TypeError(f"{label} must be an object or array")
    _validate_weighted_items(items, label)
    return items


def _weighted_pair_from_value(value: Any, label: str) -> tuple[str, float]:
    if isinstance(value, dict):
        item_label = value.get("name") or value.get("label") or value.get("value")
        weight = value.get("weight")
    elif isinstance(value, list | tuple) and len(value) == 2:
        item_label, weight = value
    else:
        raise TypeError(f"{label} entries must be pairs or objects")
    if not isinstance(item_label, str):
        raise TypeError(f"{label} entry label must be a string")
    if not isinstance(weight, int | float):
        raise TypeError(f"{label} entry weight must be numeric")
    return (item_label, float(weight))


def _validate_weighted_items(values: tuple[tuple[str, float], ...], label: str) -> None:
    if not values:
        return
    if sum(weight for _label, weight in values) <= 0:
        raise ValueError(f"{label} must have positive total weight")
    if any(weight < 0 for _label, weight in values):
        raise ValueError(f"{label} weights must be non-negative")
