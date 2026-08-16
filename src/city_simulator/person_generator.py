from __future__ import annotations

from dataclasses import dataclass

from city_simulator.agents import HouseholdAgent, PersonAgent


@dataclass(frozen=True)
class GeneratedFamily:
    household: HouseholdAgent
    people: tuple[PersonAgent, ...]
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


@dataclass(frozen=True)
class GeneratedFamilyPopulation:
    families: tuple[GeneratedFamily, ...]
    households: tuple[HouseholdAgent, ...]
    people: tuple[PersonAgent, ...]


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
        )
        for spec in specs
    )
    return GeneratedFamilyPopulation(
        families=families,
        households=tuple(family.household for family in families),
        people=tuple(person for family in families for person in family.people),
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
    support_need = _household_support_need(adults + children, housing_cost_band)
    support_capacity = _household_support_capacity(income_band, adults, adult_roles)
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
) -> tuple[PersonAgent, ...]:
    people: list[PersonAgent] = []
    for index in range(count):
        given = _pick(names["adult"], household_index + index)
        people.append(
            PersonAgent(
                _agent_id(given, family_name, str(index + 1)),
                household_id=household_id,
                display_name=f"{given} {family_name}",
                age=30 + ((household_index + index) % 35),
                income_band=income_band,
                employment_status="employed",
                role=_adult_role(adult_roles, index),
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


def _household_support_capacity(
    income_band: str,
    adult_count: int,
    adult_roles: tuple[str, ...],
) -> float:
    if adult_count <= 0:
        return 0.0
    capacities = [
        _adult_support_capacity(income_band, _adult_role(adult_roles, index))
        for index in range(adult_count)
    ]
    return sum(capacities)


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
