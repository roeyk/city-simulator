from __future__ import annotations

from dataclasses import dataclass

from city_simulator.agents import HouseholdAgent, OrganizationAgent, PersonAgent
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


def generate_family_population(
    specs: tuple[FamilyGenerationSpec, ...],
) -> GeneratedFamilyPopulation:
    families = tuple(
        generate_family_agents(
            spec.heritage,
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
        organizations=_business_organizations(family_name, household_index, jobs),
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


def _pick(values: tuple[str, ...], index: int) -> str:
    return values[index % len(values)]


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
