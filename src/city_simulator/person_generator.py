from __future__ import annotations

from dataclasses import dataclass, replace

from city_simulator.agents import (
    AdoptionIdentity,
    CulturalIdentity,
    EducationHistory,
    EmploymentRecord,
    HouseholdAgent,
    OrganizationAgent,
    PersonAgent,
)
from city_simulator.heritage_catalog import (
    canonical_heritage,
    heritage_languages,
    heritage_names,
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
    member_heritages: tuple[str, ...] = ()
    member_income_bands: tuple[str, ...] = ()
    member_ages: tuple[int | None, ...] = ()
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
    adult_income_bands: tuple[str, ...] = ()
    adult_ages: tuple[int, ...] = ()
    adult_education: tuple[str, ...] = ()
    adult_experience_years: tuple[int, ...] = ()
    preserve_income_band: bool = False


@dataclass(frozen=True)
class GeneratedFamilyPopulation:
    families: tuple[GeneratedFamily, ...]
    households: tuple[HouseholdAgent, ...]
    people: tuple[PersonAgent, ...]
    organizations: tuple[OrganizationAgent, ...]


@dataclass(frozen=True)
class CommunityInstitutionTemplate:
    culture: str
    organization_type: str
    sector: str
    display_name: str
    leader_role: str
    min_people: int = 1


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
        ("private_service", 45.0),
        ("city_service", 15.0),
        ("government", 15.0),
        ("business_owner", 20.0),
        ("faith_leader", 5.0),
    )
    community_institutions: tuple[CommunityInstitutionTemplate, ...] = (
        CommunityInstitutionTemplate(
            culture="jewish",
            organization_type="religious_institution",
            sector="faith_community",
            display_name="synagogue",
            leader_role="rabbi",
        ),
        CommunityInstitutionTemplate(
            culture="hispanic",
            organization_type="religious_institution",
            sector="faith_community",
            display_name="church",
            leader_role="priest",
        ),
        CommunityInstitutionTemplate(
            culture="hispanic",
            organization_type="religious_institution",
            sector="faith_community",
            display_name="diocese office",
            leader_role="bishop",
            min_people=15,
        ),
    )


@dataclass(frozen=True)
class SyntheticPopulationSourceProfile:
    name: str
    heritages: tuple[tuple[str, float], ...]
    household_shapes: tuple[tuple[int, int, float], ...]
    income_bands: tuple[tuple[str, float], ...]
    neighborhoods: tuple[tuple[str, str, float], ...]
    job_pools: tuple[tuple[str, float], ...]
    community_institutions: tuple[CommunityInstitutionTemplate, ...] = ()
    source_notes: tuple[str, ...] = ()

    def as_recipe(self) -> SyntheticPopulationRecipe:
        return SyntheticPopulationRecipe(
            heritages=self.heritages,
            household_shapes=self.household_shapes,
            income_bands=self.income_bands,
            neighborhoods=self.neighborhoods,
            job_pools=self.job_pools,
            community_institutions=self.community_institutions,
        )


COARSE_US_SYNTHETIC_PROFILE = SyntheticPopulationSourceProfile(
    name="coarse_us_proxy",
    heritages=(
        ("anglo", 55.0),
        ("hispanic", 30.0),
        ("jewish", 15.0),
    ),
    household_shapes=(
        (1, 0, 28.0),
        (2, 0, 22.0),
        (1, 1, 16.0),
        (2, 1, 16.0),
        (2, 2, 18.0),
    ),
    income_bands=(
        ("low", 30.0),
        ("middle", 55.0),
        ("high", 15.0),
    ),
    neighborhoods=(
        ("village_hills", "low", 25.0),
        ("summer_crescent_boulevard", "middle", 50.0),
        ("market_district", "high", 25.0),
    ),
    job_pools=(
        ("private_service", 45.0),
        ("city_service", 15.0),
        ("government", 15.0),
        ("business_owner", 20.0),
        ("faith_leader", 5.0),
    ),
    community_institutions=SyntheticPopulationRecipe().community_institutions,
    source_notes=(
        "Household shape and income weights are coarse placeholders for ACS/PUMS calibration.",
        "Education-program weights are modeled separately from NCES CIP/IPEDS completion concepts.",
        "Job-pool weights are coarse placeholders for ACS occupation and BLS employment calibration.",
        "Neighborhood weights are local scenario placeholders until Prosock neighborhood profiles are sourced.",
    ),
)


def generate_synthetic_population(
    count: int,
    recipe: SyntheticPopulationRecipe | None = None,
) -> GeneratedFamilyPopulation:
    if count < 0:
        raise ValueError("count must be non-negative")
    if recipe is None:
        recipe = COARSE_US_SYNTHETIC_PROFILE.as_recipe()
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
                adult_income_bands=_synthetic_adult_income_bands(
                    recipe.income_bands,
                    income_band,
                    household_index,
                    adults,
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
    population = generate_family_population(tuple(specs))
    return GeneratedFamilyPopulation(
        families=population.families,
        households=population.households,
        people=population.people,
        organizations=population.organizations
        + _community_organizations(population.people, recipe),
    )


def generate_family_population(
    specs: tuple[FamilyGenerationSpec, ...],
) -> GeneratedFamilyPopulation:
    families = tuple(
        generate_family_agents(
            spec.heritage,
            birth_heritages=spec.birth_heritages,
            member_heritages=spec.member_heritages,
            member_income_bands=spec.member_income_bands,
            member_ages=spec.member_ages,
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
            adult_income_bands=spec.adult_income_bands,
            adult_ages=spec.adult_ages,
            adult_education=spec.adult_education,
            adult_experience_years=spec.adult_experience_years,
            preserve_income_band=spec.preserve_income_band,
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


def enrich_synthetic_population(
    population: GeneratedFamilyPopulation,
    mixed_household_pairs: int = 0,
) -> GeneratedFamilyPopulation:
    population = _mix_culture_households(population, mixed_household_pairs)
    return _assign_schools_and_workplaces(population)


def generate_family_agents(
    heritage: str,
    birth_heritages: tuple[str, ...] = (),
    member_heritages: tuple[str, ...] = (),
    member_income_bands: tuple[str, ...] = (),
    member_ages: tuple[int | None, ...] = (),
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
    adult_income_bands: tuple[str, ...] = (),
    adult_ages: tuple[int, ...] = (),
    adult_education: tuple[str, ...] = (),
    adult_experience_years: tuple[int, ...] = (),
    preserve_income_band: bool = False,
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
    household_id = _household_id(family_name, household_index)
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
    adult_people = _adult_agents(
        names,
        family_name,
        household_id,
        household_index,
        adults,
        income_band,
        neighborhood,
        weight,
        adult_roles,
        adult_income_bands,
        ages,
        jobs,
        adult_education,
        adult_experience_years,
        cultural_identity,
        member_heritages,
        member_income_bands,
        preserve_income_band,
    )
    people = adult_people + _child_agents(
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
        member_heritages,
        member_income_bands,
        member_ages,
        tuple(person.agent_id for person in adult_people),
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
    adult_income_bands: tuple[str, ...],
    adult_ages: tuple[int, ...],
    adult_jobs: tuple[JobTemplate, ...],
    adult_education: tuple[str, ...],
    adult_experience_years: tuple[int, ...],
    identity: CulturalIdentity,
    member_heritages: tuple[str, ...],
    member_income_bands: tuple[str, ...],
    preserve_income_band: bool,
) -> tuple[PersonAgent, ...]:
    people: list[PersonAgent] = []
    for index in range(count):
        person_identity = _member_identity(identity, member_heritages, index)
        person_names = _member_names(names, member_heritages, index)
        given = _pick(person_names["adult"], household_index + index)
        job = _adult_job(adult_jobs, index)
        education = _adult_education(adult_education, index)
        experience_years = _adult_experience_years(adult_experience_years, index)
        person_income_band = _adult_person_income_band(
            _member_income_band(income_band, member_income_bands, index),
            adult_income_bands,
            job,
            education,
            experience_years,
            index,
            preserve_income_band,
        )
        employment_history = _current_employment_history(job)
        people.append(
            PersonAgent(
                _person_id(given, family_name, household_index, index),
                household_id=household_id,
                display_name=f"{given} {family_name}",
                age=adult_ages[index],
                income_band=person_income_band,
                employment_status=job.employment_status if job else "employed",
                role=job.role if job else _adult_role(adult_roles, index),
                neighborhood=neighborhood,
                identity=person_identity,
                employment_history=employment_history,
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
    member_heritages: tuple[str, ...],
    member_income_bands: tuple[str, ...],
    member_ages: tuple[int | None, ...],
    parent_ids: tuple[str, ...],
) -> tuple[PersonAgent, ...]:
    people: list[PersonAgent] = []
    for index in range(count):
        member_index = adult_count + index
        child_identity = _member_identity(raised_identity, member_heritages, member_index)
        child_names = _member_names(names, member_heritages, member_index)
        given = _pick(child_names["child"], household_index + index)
        people.append(
            PersonAgent(
                _person_id(given, family_name, household_index, member_index),
                household_id=household_id,
                display_name=f"{given} {family_name}",
                age=_child_age(member_ages, member_index, household_index, index),
                income_band=_member_income_band(income_band, member_income_bands, member_index),
                employment_status="student",
                neighborhood=neighborhood,
                parent_ids=parent_ids,
                identity=child_identity,
                adoption=_adoption_identity(child_identity, birth_heritages),
                weight=weight,
            )
        )
    return tuple(people)


def _heritage_names(heritage: str) -> dict[str, tuple[str, ...]]:
    return heritage_names(heritage)


def _member_names(
    fallback_names: dict[str, tuple[str, ...]],
    member_heritages: tuple[str, ...],
    index: int,
) -> dict[str, tuple[str, ...]]:
    if index >= len(member_heritages):
        return fallback_names
    return heritage_names(member_heritages[index])


def _cultural_identity(heritage: str) -> CulturalIdentity:
    key = canonical_heritage(heritage)
    return CulturalIdentity(
        ethnicities=(key,),
        cultures=(key,),
        languages=_heritage_languages(key),
    )


def _member_identity(
    fallback_identity: CulturalIdentity,
    member_heritages: tuple[str, ...],
    index: int,
) -> CulturalIdentity:
    if index >= len(member_heritages):
        return fallback_identity
    return _cultural_identity(member_heritages[index])


def _member_income_band(
    fallback_income_band: str,
    member_income_bands: tuple[str, ...],
    index: int,
) -> str:
    if index >= len(member_income_bands):
        return fallback_income_band
    return member_income_bands[index]


def _child_age(
    member_ages: tuple[int | None, ...],
    member_index: int,
    household_index: int,
    child_index: int,
) -> int:
    if member_index < len(member_ages) and member_ages[member_index] is not None:
        return member_ages[member_index]
    return 4 + ((household_index + child_index) % 14)


def _heritage_languages(heritage: str) -> tuple[str, ...]:
    return heritage_languages(heritage)


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


def _synthetic_adult_income_bands(
    income_bands: tuple[tuple[str, float], ...],
    household_income_band: str,
    household_index: int,
    adult_count: int,
) -> tuple[str, ...]:
    if adult_count < 2 or household_index % 3:
        return ()
    return tuple(
        _weighted_label(income_bands, household_index + index)
        for index in range(adult_count)
    )


def _community_organizations(
    people: tuple[PersonAgent, ...],
    recipe: SyntheticPopulationRecipe,
) -> tuple[OrganizationAgent, ...]:
    counts: dict[str, int] = {}
    for person in people:
        for culture in person.identity.cultures:
            counts[culture] = counts.get(culture, 0) + 1
    organizations: list[OrganizationAgent] = []
    for template in recipe.community_institutions:
        culture_count = counts.get(template.culture, 0)
        if culture_count < template.min_people:
            continue
        organizations.append(
            OrganizationAgent(
                _agent_id(template.culture, template.display_name),
                organization_type=template.organization_type,
                sector=template.sector,
                display_name=f"{template.culture.title()} {template.display_name}",
                staff=1,
                customer_types=("congregants", "residents"),
                notes=(
                    f"serves {template.culture} community",
                    f"leader role: {template.leader_role}",
                ),
            )
        )
    return tuple(organizations)


def _mix_culture_households(
    population: GeneratedFamilyPopulation,
    mixed_household_pairs: int,
) -> GeneratedFamilyPopulation:
    if mixed_household_pairs <= 0:
        return population
    people_by_id = {person.agent_id: person for person in population.people}
    households = list(population.households)
    people = list(population.people)
    people_index = {person.agent_id: index for index, person in enumerate(people)}
    candidate_ids = [
        household.agent_id
        for household in households
        if len(household.member_ids) >= 2
        and all(people_by_id[person_id].age >= 18 for person_id in household.member_ids[:2])
    ]
    mixed = 0
    for left_id, right_id in zip(candidate_ids[::2], candidate_ids[1::2], strict=False):
        if mixed >= mixed_household_pairs:
            break
        left = next(household for household in households if household.agent_id == left_id)
        right = next(household for household in households if household.agent_id == right_id)
        left_person = people_by_id[left.member_ids[1]]
        right_person = people_by_id[right.member_ids[1]]
        if left_person.identity.cultures == right_person.identity.cultures:
            continue
        swapped_left = replace(left_person, household_id=right.agent_id)
        swapped_right = replace(right_person, household_id=left.agent_id)
        people[people_index[left_person.agent_id]] = swapped_left
        people[people_index[right_person.agent_id]] = swapped_right
        people_by_id[left_person.agent_id] = swapped_left
        people_by_id[right_person.agent_id] = swapped_right
        households[households.index(left)] = replace(
            left,
            member_ids=tuple(
                right_person.agent_id if person_id == left_person.agent_id else person_id
                for person_id in left.member_ids
            ),
        )
        households[households.index(right)] = replace(
            right,
            member_ids=tuple(
                left_person.agent_id if person_id == right_person.agent_id else person_id
                for person_id in right.member_ids
            ),
        )
        mixed += 1
    return GeneratedFamilyPopulation(
        families=population.families,
        households=tuple(households),
        people=tuple(people),
        organizations=population.organizations,
    )


def _assign_schools_and_workplaces(
    population: GeneratedFamilyPopulation,
) -> GeneratedFamilyPopulation:
    baseline_organizations = (
        _school_organizations()
        + _civic_employer_organizations()
        + _basic_city_employer_organizations()
    )
    organizations = list(population.organizations + baseline_organizations)
    organization_index = {organization.agent_id: index for index, organization in enumerate(organizations)}
    business_ids = [
        organization.agent_id
        for organization in organizations
        if organization.organization_type == "business"
    ]
    owner_business_by_person = {
        owner_id: organization.agent_id
        for organization in organizations
        for owner_id in organization.owner_ids
    }
    people: list[PersonAgent] = []
    employees_by_org: dict[str, list[str]] = {organization.agent_id: [] for organization in organizations}
    for index, person in enumerate(population.people):
        updated = _assign_school(person)
        workplace_id = _workplace_for(updated, business_ids, owner_business_by_person, index)
        if workplace_id:
            employees_by_org.setdefault(workplace_id, []).append(updated.agent_id)
            updated = _assign_workplace(updated, workplace_id)
        people.append(updated)
    for organization_id, employee_ids in employees_by_org.items():
        if not employee_ids:
            continue
        organization = organizations[organization_index[organization_id]]
        organizations[organization_index[organization_id]] = replace(
            organization,
            employee_ids=tuple(dict.fromkeys(organization.employee_ids + tuple(employee_ids))),
            staff=max(organization.staff, float(len(employee_ids))),
        )
    return GeneratedFamilyPopulation(
        families=population.families,
        households=population.households,
        people=tuple(people),
        organizations=tuple(organizations),
    )


def _school_organizations() -> tuple[OrganizationAgent, ...]:
    return (
        OrganizationAgent(
            "school-elementary-1",
            organization_type="school",
            sector="education",
            display_name="Northbridge Elementary School",
            customer_types=("children", "households"),
        ),
        OrganizationAgent(
            "school-high-1",
            organization_type="high_school",
            sector="education",
            display_name="Northbridge High School",
            customer_types=("teenagers", "households"),
        ),
        OrganizationAgent(
            "college-community-1",
            organization_type="community_college",
            sector="education",
            display_name="Northbridge Community College",
            customer_types=("students", "workers"),
        ),
    )


def _civic_employer_organizations() -> tuple[OrganizationAgent, ...]:
    return (
        OrganizationAgent(
            "mayor-office-1",
            organization_type="government",
            sector="public_administration",
            display_name="Northbridge Mayor Office",
            customer_types=("residents", "businesses", "institutions"),
        ),
        OrganizationAgent(
            "city-council-1",
            organization_type="government",
            sector="public_administration",
            display_name="Northbridge City Council",
            customer_types=("residents", "businesses"),
        ),
        OrganizationAgent(
            "city-planning-1",
            organization_type="government",
            sector="planning",
            display_name="Northbridge Planning Department",
            customer_types=("residents", "businesses", "developers"),
        ),
        OrganizationAgent(
            "city-services-1",
            organization_type="government",
            sector="city_services",
            display_name="Northbridge City Services",
            customer_types=("residents", "businesses"),
        ),
        OrganizationAgent(
            "city-hall-1",
            organization_type="government",
            sector="public_administration",
            display_name="Northbridge City Hall",
            customer_types=("residents", "businesses"),
        ),
    )


def _basic_city_employer_organizations() -> tuple[OrganizationAgent, ...]:
    return (
        OrganizationAgent(
            "grocery-1",
            organization_type="grocery_store",
            sector="grocery",
            neighborhood="market_district",
            display_name="Market District Grocery",
            customer_types=("residents",),
        ),
        OrganizationAgent(
            "restaurant-1",
            organization_type="restaurant",
            sector="food_service",
            neighborhood="market_district",
            display_name="Market District Diner",
            customer_types=("residents", "visitors"),
        ),
        OrganizationAgent(
            "hospital-1",
            organization_type="hospital",
            sector="medical",
            neighborhood="summer_crescent_boulevard",
            display_name="Crescent General Hospital",
            customer_types=("residents", "regional_patients"),
        ),
        OrganizationAgent(
            "school-district-1",
            organization_type="school_district",
            sector="education",
            neighborhood="village_hills",
            display_name="Village Hills Schools",
            customer_types=("children", "households"),
        ),
        OrganizationAgent(
            "warehouse-1",
            organization_type="regional_warehouse",
            sector="logistics",
            neighborhood="market_district",
            display_name="Market District Warehouse",
            customer_types=("businesses", "institutions"),
        ),
    )


def _assign_school(person: PersonAgent) -> PersonAgent:
    if person.age < 14:
        school_id = "school-elementary-1"
    elif person.age < 18:
        school_id = "school-high-1"
    elif person.age <= 24:
        school_id = "college-community-1"
    else:
        return person
    return replace(
        person,
        current_school_id=school_id,
        education_history=_education_history_with_school(person.education_history, school_id, person.age),
    )


def _education_history_with_school(
    history: EducationHistory,
    school_id: str,
    age: int,
) -> EducationHistory:
    if school_id.startswith("school-elementary"):
        return replace(history, grade_school_ids=(school_id,))
    if school_id.startswith("school-high"):
        return replace(history, high_school_ids=(school_id,))
    return replace(history, college_ids=(school_id,))


def _workplace_for(
    person: PersonAgent,
    business_ids: list[str],
    owner_business_by_person: dict[str, str],
    index: int,
) -> str:
    if person.employment_status == "student" or not person.role:
        return ""
    if person.employment_status == "business_owner":
        return owner_business_by_person.get(person.agent_id, "")
    if person.role == "mayor":
        return "mayor-office-1"
    if person.role in {"city council member", "legislative aide"}:
        return "city-council-1"
    if person.role in {"city planner", "building inspector"}:
        return "city-planning-1"
    if person.role in {"firefighter", "police officer", "waterworks operator"}:
        return "city-services-1"
    if person.role in {
        "city judge",
        "court clerk",
        "public works administrator",
    }:
        return "city-hall-1"
    if person.role in {"medical assistant"}:
        return "hospital-1"
    if person.role in {"retail salesperson"}:
        return "grocery-1"
    if person.role in {"restaurant server"}:
        return "restaurant-1"
    if person.role in {"bookkeeper"}:
        return "warehouse-1"
    if not business_ids:
        return ""
    return business_ids[index % len(business_ids)]


def _assign_workplace(person: PersonAgent, workplace_id: str) -> PersonAgent:
    history = person.employment_history
    if history:
        history = (replace(history[0], workplace_id=workplace_id),) + history[1:]
    return replace(person, workplace_id=workplace_id, employment_history=history)


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


def _household_id(family_name: str, household_index: int) -> str:
    return _agent_id("household", f"{household_index + 1:04d}", family_name)


def _person_id(given: str, family_name: str, household_index: int, member_index: int) -> str:
    return _agent_id("person", f"{household_index + 1:04d}", f"{member_index + 1:02d}", given, family_name)


def _adult_person_income_band(
    fallback_income_band: str,
    adult_income_bands: tuple[str, ...],
    job: JobTemplate | None,
    education: str,
    experience_years: int,
    index: int,
    preserve_income_band: bool,
) -> str:
    if adult_income_bands:
        return adult_income_bands[index] if index < len(adult_income_bands) else fallback_income_band
    if preserve_income_band:
        return fallback_income_band
    return _adult_generated_income_band(fallback_income_band, job, education, experience_years)


def _current_employment_history(job: JobTemplate | None) -> tuple[EmploymentRecord, ...]:
    if job is None:
        return ()
    return (
        EmploymentRecord(
            workplace_id="",
            role=job.role,
            start_year=0,
            employment_status=job.employment_status,
            sector=job.sector,
        ),
    )


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


def _adult_generated_income_band(
    fallback_income_band: str,
    job: JobTemplate | None,
    education: str,
    experience_years: int,
) -> str:
    if job is None:
        return fallback_income_band
    entry_band = job.entry_income_band or job.income_band
    experienced_band = job.experienced_income_band or job.income_band
    if experience_years < max(job.min_experience_years + 5, 8):
        return entry_band
    if _education_rank(education) < _education_rank(job.required_education):
        return entry_band
    return experienced_band


def _education_rank(education: str) -> int:
    ranks = {
        "none": 0,
        "high_school": 1,
        "trade": 2,
        "college": 3,
        "graduate": 4,
    }
    return ranks.get(education, 0)


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
                employee_ids=(people[index].agent_id,),
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
