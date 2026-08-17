from __future__ import annotations

from dataclasses import dataclass

from city_simulator.agents import (
    AdoptionIdentity,
    CulturalIdentity,
    HouseholdAgent,
    OrganizationAgent,
    PersonAgent,
)
from city_simulator.work_catalog import JobTemplate, eligible_job_template_for


@dataclass(frozen=True)
class GeneratedFamily:
    household: HouseholdAgent
    people: tuple[PersonAgent, ...]
    organizations: tuple[OrganizationAgent, ...]
    support_need: float
    support_capacity: float
    support_gap: float


@dataclass(frozen=True)
class FamilyGenerationSpec:
    heritage: str
    birth_heritages: tuple[str, ...] = ()
    household_index: int = 0
    adults: int = 2
    children: int = 0
    income_band: str = "middle"
    neighborhood: str | None = None
    housing_cost_band: str = "middle"
    weight: float = 1.0
    adult_roles: tuple[str, ...] = ()
    adult_jobs: tuple[JobTemplate, ...] = ()
    job_pools: tuple[str, ...] = ()
    adult_ages: tuple[int, ...] = ()
    adult_education: tuple[str, ...] = ()
    adult_experience_years: tuple[int, ...] = ()


@dataclass(frozen=True)
class GeneratedFamilyPopulation:
    families: tuple[GeneratedFamily, ...]
    households: tuple[HouseholdAgent, ...]
    people: tuple[PersonAgent, ...]
    organizations: tuple[OrganizationAgent, ...]


@dataclass(frozen=True)
class SyntheticPopulationRecipe:
    heritages: tuple[tuple[str, float], ...] = (
        ("anglo", 55.0),
        ("hispanic", 30.0),
        ("jewish", 15.0),
    )
    household_shapes: tuple[tuple[int, int, float], ...] = (
        (1, 0, 28.0),
        (2, 0, 22.0),
        (1, 1, 16.0),
        (2, 1, 16.0),
        (2, 2, 18.0),
    )
    income_bands: tuple[tuple[str, float], ...] = (
        ("low", 30.0),
        ("middle", 55.0),
        ("high", 15.0),
    )
    neighborhoods: tuple[tuple[str, str, float], ...] = (
        ("village_hills", "low", 25.0),
        ("summer_crescent_boulevard", "middle", 50.0),
        ("market_district", "high", 25.0),
    )
    job_pools: tuple[tuple[str, float], ...] = (
        ("private_service", 50.0),
        ("city_service", 15.0),
        ("government", 15.0),
        ("business_owner", 20.0),
    )


HERITAGE_NAMES: dict[str, dict[str, tuple[str, ...]]] = {
    "hispanic": {
        "family": ("Hernandez", "Garcia", "Martinez", "Lopez", "Rivera"),
        "adult": ("Juan", "Louise", "Carlos", "Marisol", "Elena", "Miguel"),
        "child": ("Renee", "Jose", "Sofia", "Diego", "Lucia", "Mateo"),
    },
    "anglo": {
        "family": ("Jones", "Harcourt", "Korr", "Miller", "Bennett"),
        "adult": ("Dorothy", "Ron", "Jane", "John", "Anne", "Robert"),
        "child": ("Morty", "Emily", "Thomas", "Grace", "Henry", "Claire"),
    },
    "jewish": {
        "family": ("Katan", "Cohen", "Levine", "Rosen", "Shapiro"),
        "adult": ("Yossi", "Miriam", "Ari", "Leah", "Noam", "Talia"),
        "child": ("Eli", "Naomi", "Avi", "Maya", "Dina", "Jonah"),
    },
}


def generate_synthetic_population(
    count: int,
    recipe: SyntheticPopulationRecipe | None = None,
) -> GeneratedFamilyPopulation:
    if count < 0:
        raise ValueError("count must be non-negative")
    if recipe is None:
        recipe = SyntheticPopulationRecipe()
    specs: list[FamilyGenerationSpec] = []
    remaining = count
    household_index = 0
    while remaining > 0:
        adults, children = _synthetic_household_shape(recipe, household_index, remaining)
        income_band = _weighted_label(recipe.income_bands, household_index * 2)
        neighborhood, housing_cost_band = _synthetic_neighborhood(recipe, household_index)
        adult_ages = tuple(24 + ((household_index + index) * 7 % 42) for index in range(adults))
        adult_education = tuple(
            _synthetic_education(income_band, household_index + index)
            for index in range(adults)
        )
        specs.append(
            FamilyGenerationSpec(
                _weighted_label(recipe.heritages, household_index),
                household_index=household_index,
                adults=adults,
                children=children,
                income_band=income_band,
                neighborhood=neighborhood,
                housing_cost_band=housing_cost_band,
                job_pools=tuple(
                    _weighted_label(recipe.job_pools, household_index + index)
                    for index in range(adults)
                ),
                adult_ages=adult_ages,
                adult_education=adult_education,
                adult_experience_years=tuple(
                    max(age - 22, 1) for age in adult_ages
                ),
            )
        )
        remaining -= adults + children
        household_index += 1
    return generate_family_population(tuple(specs))


def generate_family_population(
    specs: tuple[FamilyGenerationSpec, ...],
) -> GeneratedFamilyPopulation:
    families = tuple(
        generate_family_agents(
            spec.heritage,
            birth_heritages=spec.birth_heritages,
            household_index=spec.household_index,
            adults=spec.adults,
            children=spec.children,
            income_band=spec.income_band,
            neighborhood=spec.neighborhood,
            housing_cost_band=spec.housing_cost_band,
            weight=spec.weight,
            adult_roles=spec.adult_roles,
            adult_jobs=spec.adult_jobs,
            job_pools=spec.job_pools,
            adult_ages=spec.adult_ages,
            adult_education=spec.adult_education,
            adult_experience_years=spec.adult_experience_years,
        )
        for spec in specs
    )
    return GeneratedFamilyPopulation(
        families=families,
        households=tuple(family.household for family in families),
        people=tuple(person for family in families for person in family.people),
        organizations=tuple(
            organization for family in families for organization in family.organizations
        ),
    )


def generate_family_agents(
    heritage: str,
    birth_heritages: tuple[str, ...] = (),
    household_index: int = 0,
    adults: int = 2,
    children: int = 0,
    income_band: str = "middle",
    neighborhood: str | None = None,
    housing_cost_band: str = "middle",
    weight: float = 1.0,
    adult_roles: tuple[str, ...] = (),
    adult_jobs: tuple[JobTemplate, ...] = (),
    job_pools: tuple[str, ...] = (),
    adult_ages: tuple[int, ...] = (),
    adult_education: tuple[str, ...] = (),
    adult_experience_years: tuple[int, ...] = (),
) -> GeneratedFamily:
    if adults < 0 or children < 0:
        raise ValueError("adults and children must be non-negative")
    if adults + children <= 0:
        raise ValueError("family must include at least one person")
    if weight <= 0:
        raise ValueError("weight must be positive")
    _validate_housing_cost_band(housing_cost_band)
    names = _heritage_names(heritage)
    cultural_identity = _cultural_identity(heritage)
    family_name = _pick(names["family"], household_index)
    household_id = _agent_id(family_name)
    ages = _adult_ages(household_index, adults, adult_ages)
    _validate_adult_ages(ages)
    jobs = _adult_jobs(
        adult_jobs,
        job_pools,
        household_index,
        ages,
        adult_education,
        adult_experience_years,
    )
    support_need = _household_support_need(adults + children, housing_cost_band)
    support_capacity = _household_support_capacity(income_band, adults, adult_roles, jobs)
    support_gap = max(support_need - support_capacity, 0.0)
    people = _adult_agents(
        names,
        family_name,
        household_id,
        household_index,
        adults,
        income_band,
        neighborhood,
        weight,
        adult_roles,
        ages,
        jobs,
        cultural_identity,
    ) + _child_agents(
        names,
        family_name,
        household_id,
        household_index,
        adults,
        children,
        income_band,
        neighborhood,
        weight,
        cultural_identity,
        birth_heritages,
    )
    return GeneratedFamily(
        household=HouseholdAgent(
            household_id,
            member_ids=tuple(person.agent_id for person in people),
            income_band=income_band,
            neighborhood=neighborhood,
            weight=weight,
            notes=_household_notes(support_need, support_capacity, housing_cost_band),
        ),
        people=people,
        organizations=_business_organizations(family_name, household_index, jobs, people),
        support_need=support_need,
        support_capacity=support_capacity,
        support_gap=support_gap,
    )


def _adult_agents(
    names: dict[str, tuple[str, ...]],
    family_name: str,
    household_id: str,
    household_index: int,
    count: int,
    income_band: str,
    neighborhood: str | None,
    weight: float,
    adult_roles: tuple[str, ...],
    adult_ages: tuple[int, ...],
    adult_jobs: tuple[JobTemplate, ...],
    identity: CulturalIdentity,
) -> tuple[PersonAgent, ...]:
    people: list[PersonAgent] = []
    for index in range(count):
        given = _pick(names["adult"], household_index + index)
        job = _adult_job(adult_jobs, index)
        people.append(
            PersonAgent(
                _agent_id(given, family_name, str(index + 1)),
                household_id=household_id,
                display_name=f"{given} {family_name}",
                age=adult_ages[index],
                income_band=job.income_band if job else income_band,
                employment_status=job.employment_status if job else "employed",
                role=job.role if job else _adult_role(adult_roles, index),
                neighborhood=neighborhood,
                identity=identity,
                weight=weight,
            )
        )
    return tuple(people)


def _child_agents(
    names: dict[str, tuple[str, ...]],
    family_name: str,
    household_id: str,
    household_index: int,
    adult_count: int,
    count: int,
    income_band: str,
    neighborhood: str | None,
    weight: float,
    raised_identity: CulturalIdentity,
    birth_heritages: tuple[str, ...],
) -> tuple[PersonAgent, ...]:
    people: list[PersonAgent] = []
    for index in range(count):
        given = _pick(names["child"], household_index + index)
        people.append(
            PersonAgent(
                _agent_id(given, family_name, str(adult_count + index + 1)),
                household_id=household_id,
                display_name=f"{given} {family_name}",
                age=4 + ((household_index + index) % 14),
                income_band=income_band,
                employment_status="student",
                neighborhood=neighborhood,
                parent_ids=tuple(
                    _agent_id(
                        _pick(names["adult"], household_index + parent_index),
                        family_name,
                        str(parent_index + 1),
                    )
                    for parent_index in range(adult_count)
                ),
                identity=raised_identity,
                adoption=_adoption_identity(raised_identity, birth_heritages),
                weight=weight,
            )
        )
    return tuple(people)


def _heritage_names(heritage: str) -> dict[str, tuple[str, ...]]:
    key = heritage.lower()
    if key not in HERITAGE_NAMES:
        choices = ", ".join(sorted(HERITAGE_NAMES))
        raise ValueError(f"unknown heritage {heritage!r}; choose one of: {choices}")
    return HERITAGE_NAMES[key]


def _cultural_identity(heritage: str) -> CulturalIdentity:
    key = heritage.lower()
    return CulturalIdentity(
        ethnicities=(key,),
        cultures=(key,),
        languages=_heritage_languages(key),
    )


def _heritage_languages(heritage: str) -> tuple[str, ...]:
    match heritage:
        case "hispanic":
            return ("english", "spanish")
        case "jewish":
            return ("english", "hebrew")
        case _:
            return ("english",)


def _adoption_identity(
    raised_identity: CulturalIdentity,
    birth_heritages: tuple[str, ...],
) -> AdoptionIdentity:
    if not birth_heritages:
        return AdoptionIdentity()
    birth_identities = tuple(_cultural_identity(heritage) for heritage in birth_heritages)
    return AdoptionIdentity(
        is_adopted=True,
        birth_parent_ethnicities=tuple(
            ethnicity
            for identity in birth_identities
            for ethnicity in identity.ethnicities
        ),
        birth_parent_cultures=tuple(
            culture for identity in birth_identities for culture in identity.cultures
        ),
        adoptive_parent_ethnicities=raised_identity.ethnicities,
        adoptive_parent_cultures=raised_identity.cultures,
        raised_cultures=raised_identity.cultures,
    )


def _synthetic_household_shape(
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
    return _weighted_household_shape(fitting_shapes, household_index)


def _synthetic_neighborhood(
    recipe: SyntheticPopulationRecipe,
    household_index: int,
) -> tuple[str, str]:
    return _weighted_neighborhood(recipe.neighborhoods, household_index)


def _synthetic_education(income_band: str, index: int) -> str:
    match income_band:
        case "high":
            choices = (("college", 60.0), ("graduate", 40.0))
        case "middle":
            choices = (("high_school", 35.0), ("trade", 30.0), ("college", 35.0))
        case _:
            choices = (("high_school", 70.0), ("trade", 25.0), ("college", 5.0))
    return _weighted_label(choices, index)


def _weighted_label(values: tuple[tuple[str, float], ...], index: int) -> str:
    total = sum(weight for _label, weight in values)
    if total <= 0:
        raise ValueError("weighted choices must have positive total weight")
    target = _weighted_target(index, total)
    cumulative = 0
    for label, weight in values:
        cumulative += round(weight)
        if target < cumulative:
            return label
    return values[-1][0]


def _weighted_household_shape(
    values: tuple[tuple[int, int, float], ...],
    index: int,
) -> tuple[int, int]:
    total = sum(weight for _adults, _children, weight in values)
    if total <= 0:
        raise ValueError("weighted choices must have positive total weight")
    target = _weighted_target(index, total)
    cumulative = 0
    for adults, children, weight in values:
        cumulative += round(weight)
        if target < cumulative:
            return (adults, children)
    adults, children, _weight = values[-1]
    return (adults, children)


def _weighted_neighborhood(
    values: tuple[tuple[str, str, float], ...],
    index: int,
) -> tuple[str, str]:
    total = sum(weight for _neighborhood, _housing_cost_band, weight in values)
    if total <= 0:
        raise ValueError("weighted choices must have positive total weight")
    target = _weighted_target(index, total)
    cumulative = 0
    for neighborhood, housing_cost_band, weight in values:
        cumulative += round(weight)
        if target < cumulative:
            return (neighborhood, housing_cost_band)
    neighborhood, housing_cost_band, _weight = values[-1]
    return (neighborhood, housing_cost_band)


def _pick(values: tuple[str, ...], index: int) -> str:
    return values[index % len(values)]


def _weighted_target(index: int, total: float) -> int:
    return (index * 37) % round(total)


def _agent_id(*parts: str) -> str:
    return "-".join(part.lower().replace(" ", "-") for part in parts if part)


def _adult_role(roles: tuple[str, ...], index: int) -> str:
    if not roles:
        return ""
    return roles[index] if index < len(roles) else roles[-1]


def _adult_ages(
    household_index: int,
    adult_count: int,
    adult_ages: tuple[int, ...],
) -> tuple[int, ...]:
    if adult_ages:
        return tuple(
            adult_ages[index] if index < len(adult_ages) else adult_ages[-1]
            for index in range(adult_count)
        )
    return tuple(30 + ((household_index + index) % 35) for index in range(adult_count))


def _validate_adult_ages(adult_ages: tuple[int, ...]) -> None:
    if any(age < 18 for age in adult_ages):
        raise ValueError("adult family members must be at least 18 years old")


def _adult_jobs(
    adult_jobs: tuple[JobTemplate, ...],
    job_pools: tuple[str, ...],
    household_index: int,
    adult_ages: tuple[int, ...],
    adult_education: tuple[str, ...],
    adult_experience_years: tuple[int, ...],
) -> tuple[JobTemplate, ...]:
    if adult_jobs:
        return adult_jobs
    if not job_pools:
        return ()
    return tuple(
        eligible_job_template_for(
            _adult_role(job_pools, index),
            household_index + index,
            adult_ages[index],
            _adult_education(adult_education, index),
            _adult_experience_years(adult_experience_years, index),
        )
        for index in range(len(adult_ages))
    )


def _adult_job(adult_jobs: tuple[JobTemplate, ...], index: int) -> JobTemplate | None:
    if not adult_jobs:
        return None
    return adult_jobs[index] if index < len(adult_jobs) else adult_jobs[-1]


def _adult_education(adult_education: tuple[str, ...], index: int) -> str:
    if not adult_education:
        return "high_school"
    return adult_education[index] if index < len(adult_education) else adult_education[-1]


def _adult_experience_years(adult_experience_years: tuple[int, ...], index: int) -> int:
    if not adult_experience_years:
        return 5
    return (
        adult_experience_years[index]
        if index < len(adult_experience_years)
        else adult_experience_years[-1]
    )


def _household_support_capacity(
    income_band: str,
    adult_count: int,
    adult_roles: tuple[str, ...],
    adult_jobs: tuple[JobTemplate, ...],
) -> float:
    if adult_count <= 0:
        return 0.0
    capacities = [
        _adult_support_capacity(
            _adult_income_band(income_band, adult_jobs, index),
            _adult_work_role(adult_roles, adult_jobs, index),
        )
        for index in range(adult_count)
    ]
    return sum(capacities)


def _adult_income_band(
    fallback_income_band: str,
    adult_jobs: tuple[JobTemplate, ...],
    index: int,
) -> str:
    job = _adult_job(adult_jobs, index)
    return job.income_band if job else fallback_income_band


def _adult_work_role(
    adult_roles: tuple[str, ...],
    adult_jobs: tuple[JobTemplate, ...],
    index: int,
) -> str:
    job = _adult_job(adult_jobs, index)
    return job.role if job else _adult_role(adult_roles, index)


def _adult_support_capacity(income_band: str, role: str) -> float:
    role_key = role.lower()
    if any(marker in role_key for marker in ("retail", "cashier", "server", "receptionist")):
        return 2.0
    match income_band:
        case "low":
            return 1.5
        case "middle":
            return 3.0
        case "high":
            return 4.5
        case _:
            return 2.0


def _household_support_need(family_size: int, housing_cost_band: str) -> float:
    match housing_cost_band:
        case "low":
            housing_pressure = -0.5
        case "middle":
            housing_pressure = 0.0
        case "high":
            housing_pressure = 1.0
        case _:
            housing_pressure = 0.0
    return max(family_size + housing_pressure, 1.0)


def _business_organizations(
    family_name: str,
    household_index: int,
    adult_jobs: tuple[JobTemplate, ...],
    people: tuple[PersonAgent, ...],
) -> tuple[OrganizationAgent, ...]:
    organizations: list[OrganizationAgent] = []
    for index, job in enumerate(adult_jobs):
        if job.employment_status != "business_owner":
            continue
        organizations.append(
            OrganizationAgent(
                _agent_id(family_name, job.sector, str(household_index + index)),
                organization_type=job.organization_type or "business",
                sector=job.sector,
                display_name=f"{family_name} {job.sector.replace('_', ' ')}",
                owner_ids=(people[index].agent_id,),
                customer_types=job.serves,
                notes=tuple(f"serves {customer}" for customer in job.serves),
            )
        )
    return tuple(organizations)


def _validate_housing_cost_band(housing_cost_band: str) -> None:
    if housing_cost_band not in {"low", "middle", "high"}:
        raise ValueError("housing_cost_band must be one of: high, low, middle")


def _household_notes(
    support_need: float,
    support_capacity: float,
    housing_cost_band: str,
) -> tuple[str, ...]:
    if support_need <= support_capacity:
        return ()
    return (
        f"financial strain: {housing_cost_band} housing cost exceeds adult earning support capacity",
    )
