from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Agent:
    agent_id: str
    weight: float = field(default=1.0, kw_only=True)


@dataclass(frozen=True)
class CulturalAffiliation:
    culture: str
    strength: float = 1.0
    source: str = ""
    home_use: bool = False
    community_use: bool = False
    self_identified: bool = True
    years_affiliated: float = 0.0
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CulturalIdentity:
    ethnicities: tuple[str, ...] = ()
    cultures: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    religion: str = ""
    religiosity: str = ""
    affiliations: tuple[CulturalAffiliation, ...] = ()

    def __post_init__(self) -> None:
        if not self.affiliations and self.cultures:
            object.__setattr__(
                self,
                "affiliations",
                cultural_affiliations_from_cultures(self.cultures),
            )

    def affiliation_for(self, culture: str) -> CulturalAffiliation | None:
        return next(
            (affiliation for affiliation in self.affiliations if affiliation.culture == culture),
            None,
        )

    def strength_for(self, culture: str) -> float:
        affiliation = self.affiliation_for(culture)
        if affiliation is None:
            return 0.0
        return affiliation.strength


def cultural_affiliations_from_cultures(
    cultures: tuple[str, ...],
) -> tuple[CulturalAffiliation, ...]:
    return tuple(
        CulturalAffiliation(
            culture=culture,
            strength=1.0,
            source="legacy_culture",
            home_use=True,
            community_use=True,
            self_identified=True,
        )
        for culture in cultures
    )


_PROFICIENCY_RANKS = {
    "none": 0,
    "basic": 1,
    "conversational": 2,
    "professional": 3,
    "native": 4,
}


@dataclass(frozen=True)
class LanguageSkill:
    language: str
    spoken_proficiency: str = "conversational"
    reading_proficiency: str = "conversational"
    writing_proficiency: str = "conversational"
    home_use: bool = False
    work_use: bool = False
    needs_interpreter: bool = False
    years_learning: float = 0.0
    arrival_proficiency: str = ""
    learning_contexts: tuple[str, ...] = ()
    exposure_score: float = 0.0
    last_year_practice_hours: float = 0.0

    @property
    def spoken_rank(self) -> int:
        return _PROFICIENCY_RANKS.get(self.spoken_proficiency, 0)

    def can_bridge(self, minimum: str = "professional") -> bool:
        return self.spoken_rank >= _PROFICIENCY_RANKS.get(minimum, 3)


@dataclass(frozen=True)
class LanguageProfile:
    skills: tuple[LanguageSkill, ...] = ()
    household_languages: tuple[str, ...] = ()
    preferred_language: str = ""
    interpreter_needed: bool = False

    @property
    def languages(self) -> tuple[str, ...]:
        return tuple(skill.language for skill in self.skills)

    def skill_for(self, language: str) -> LanguageSkill | None:
        return next((skill for skill in self.skills if skill.language == language), None)

    def spoken_rank(self, language: str) -> int:
        skill = self.skill_for(language)
        if skill is None:
            return 0
        return skill.spoken_rank

    def shared_spoken_rank(self, other: LanguageProfile) -> int:
        return max(
            (
                min(self.spoken_rank(language), other.spoken_rank(language))
                for language in set(self.languages) & set(other.languages)
            ),
            default=0,
        )


@dataclass(frozen=True)
class ServiceLanguage:
    language: str
    service_proficiency: str = "professional"
    staff_capacity: float = 0.0
    interpreter_capacity: float = 0.0
    tags: tuple[str, ...] = ()

    @property
    def service_rank(self) -> int:
        return _PROFICIENCY_RANKS.get(self.service_proficiency, 0)


def language_profile_from_languages(languages: tuple[str, ...]) -> LanguageProfile:
    return LanguageProfile(
        skills=tuple(
            LanguageSkill(
                language=language,
                spoken_proficiency="native",
                reading_proficiency="native",
                writing_proficiency="native",
                home_use=True,
            )
            for language in languages
        ),
        household_languages=languages,
        preferred_language=languages[0] if languages else "",
    )


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
    language_profile: LanguageProfile = field(default_factory=LanguageProfile)
    adoption: AdoptionIdentity = field(default_factory=AdoptionIdentity)
    workplace_id: str = ""
    current_school_id: str = ""
    education_history: EducationHistory = field(default_factory=EducationHistory)
    employment_history: tuple[EmploymentRecord, ...] = ()
    health_conditions: tuple[str, ...] = ()
    debts: tuple[str, ...] = ()
    assets: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.language_profile.skills and self.identity.languages:
            object.__setattr__(
                self,
                "language_profile",
                language_profile_from_languages(self.identity.languages),
            )

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
    household_languages: tuple[str, ...] = ()
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
    employee_ids: tuple[str, ...] = ()
    founded_year: int | None = None
    customer_types: tuple[str, ...] = ()
    service_languages: tuple[ServiceLanguage, ...] = ()
    notes: tuple[str, ...] = ()
