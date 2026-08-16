from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Agent:
    agent_id: str
    weight: float = field(default=1.0, kw_only=True)


@dataclass(frozen=True)
class CulturalIdentity:
    ethnicities: tuple[str, ...] = ()
    cultures: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    religion: str = ""
    religiosity: str = ""


@dataclass(frozen=True)
class AdoptionIdentity:
    is_adopted: bool = False
    birth_parent_ethnicities: tuple[str, ...] = ()
    birth_parent_cultures: tuple[str, ...] = ()
    adoptive_parent_ethnicities: tuple[str, ...] = ()
    adoptive_parent_cultures: tuple[str, ...] = ()
    raised_cultures: tuple[str, ...] = ()


@dataclass(frozen=True)
class EducationCompletion:
    institution_id: str
    graduation_year: int
    credential: str = ""
    discipline: str = ""
    major: str = ""
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class EducationHistory:
    daycare_ids: tuple[str, ...] = ()
    grade_school_ids: tuple[str, ...] = ()
    high_school_ids: tuple[str, ...] = ()
    college_ids: tuple[str, ...] = ()
    trade_school_ids: tuple[str, ...] = ()
    masters_university_ids: tuple[str, ...] = ()
    phd_university_ids: tuple[str, ...] = ()
    graduations: tuple[EducationCompletion, ...] = ()


@dataclass(frozen=True)
class EmploymentRecord:
    workplace_id: str
    role: str
    start_year: int
    end_year: int | None = None
    employment_status: str = "employed"
    sector: str = ""
    skills_used: tuple[str, ...] = ()


@dataclass(frozen=True)
class PersonAgent(Agent):
    household_id: str
    age: int
    income_band: str
    employment_status: str = "not_in_labor_force"
    health_status: str = "typical"
    neighborhood: str | None = None
    display_name: str = ""
    role: str = ""
    housing_status: str = ""
    parent_ids: tuple[str, ...] = ()
    identity: CulturalIdentity = field(default_factory=CulturalIdentity)
    adoption: AdoptionIdentity = field(default_factory=AdoptionIdentity)
    workplace_id: str = ""
    current_school_id: str = ""
    education_history: EducationHistory = field(default_factory=EducationHistory)
    employment_history: tuple[EmploymentRecord, ...] = ()
    health_conditions: tuple[str, ...] = ()
    debts: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def is_child(self) -> bool:
        return self.age < 18

    @property
    def is_working_age(self) -> bool:
        return 18 <= self.age < 65

    @property
    def is_senior(self) -> bool:
        return self.age >= 65


@dataclass(frozen=True)
class HouseholdAgent(Agent):
    member_ids: tuple[str, ...]
    income_band: str
    tenure: str = "unknown"
    neighborhood: str | None = None
    housing_status: str = ""
    debts: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class LivingConditions:
    household_id: str
    income_band: str
    tenure: str
    housing_status: str
    neighborhood: str | None = None


def living_conditions_for(person: PersonAgent, household: HouseholdAgent) -> LivingConditions:
    return LivingConditions(
        household_id=household.agent_id,
        income_band=person.income_band or household.income_band,
        tenure=household.tenure,
        housing_status=person.housing_status or household.housing_status,
        neighborhood=person.neighborhood or household.neighborhood,
    )


@dataclass(frozen=True)
class OrganizationAgent(Agent):
    organization_type: str
    sector: str = "unspecified"
    neighborhood: str | None = None
    staff: float = 0.0
    operating_budget: float = 0.0
    display_name: str = ""
    owner_ids: tuple[str, ...] = ()
    founded_year: int | None = None
    customer_types: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
