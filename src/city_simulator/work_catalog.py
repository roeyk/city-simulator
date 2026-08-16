from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class JobTemplate:
    role: str
    employment_status: str
    income_band: str
    employer_type: str
    sector: str
    branch: str = ""
    serves: tuple[str, ...] = ()
    organization_type: str = ""
    min_age: int = 18
    required_education: str = "none"
    min_experience_years: int = 0


@dataclass(frozen=True)
class BusinessType:
    sector: str
    display_name: str
    customer_types: tuple[str, ...]
    typical_owner_role: str
    income_band: str = "middle"


@dataclass(frozen=True)
class TradeSchoolProgram:
    program: str
    sector: str
    credential: str = "certificate"
    discipline: str = "skilled trades"
    typical_skills: tuple[str, ...] = ()
    prepares_for_roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class CollegeProgram:
    major: str
    discipline: str
    credential_levels: tuple[str, ...] = ("bachelors",)
    typical_skills: tuple[str, ...] = ()
    prepares_for_roles: tuple[str, ...] = ()


CITY_SERVICE_JOBS: tuple[JobTemplate, ...] = (
    JobTemplate(
        role="firefighter",
        employment_status="employed",
        income_band="middle",
        employer_type="city_service",
        sector="fire_services",
        serves=("residents", "businesses"),
        organization_type="government",
    ),
    JobTemplate(
        role="police officer",
        employment_status="employed",
        income_band="middle",
        employer_type="city_service",
        sector="police_services",
        serves=("residents", "businesses"),
        organization_type="government",
    ),
    JobTemplate(
        role="waterworks operator",
        employment_status="employed",
        income_band="middle",
        employer_type="city_service",
        sector="water_utility",
        serves=("residents", "businesses"),
        organization_type="government",
    ),
)


GOVERNMENT_JOBS: tuple[JobTemplate, ...] = (
    JobTemplate(
        role="city judge",
        employment_status="employed",
        income_band="high",
        employer_type="government",
        sector="public_administration",
        branch="judicial",
        serves=("residents", "businesses"),
        organization_type="government",
        min_age=35,
        required_education="graduate",
        min_experience_years=10,
    ),
    JobTemplate(
        role="court clerk",
        employment_status="employed",
        income_band="middle",
        employer_type="government",
        sector="public_administration",
        branch="judicial",
        serves=("residents",),
        organization_type="government",
    ),
    JobTemplate(
        role="legislative aide",
        employment_status="employed",
        income_band="middle",
        employer_type="government",
        sector="public_administration",
        branch="legislative",
        serves=("residents", "businesses"),
        organization_type="government",
    ),
    JobTemplate(
        role="public works administrator",
        employment_status="employed",
        income_band="middle",
        employer_type="government",
        sector="public_administration",
        branch="executive",
        serves=("residents", "businesses"),
        organization_type="government",
    ),
    JobTemplate(
        role="building inspector",
        employment_status="employed",
        income_band="middle",
        employer_type="regulatory_agency",
        sector="public_administration",
        branch="regulatory",
        serves=("residents", "businesses"),
        organization_type="government",
    ),
)


COLLEGE_PROGRAMS: tuple[CollegeProgram, ...] = (
    CollegeProgram(
        major="business administration",
        discipline="business",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("management", "accounting", "operations"),
        prepares_for_roles=("business manager", "business owner", "operations analyst"),
    ),
    CollegeProgram(
        major="accounting",
        discipline="business",
        credential_levels=("bachelors", "masters"),
        typical_skills=("bookkeeping", "tax accounting", "audit preparation"),
        prepares_for_roles=("accountant", "bookkeeper", "financial controller"),
    ),
    CollegeProgram(
        major="finance",
        discipline="business",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("financial analysis", "portfolio analysis", "risk assessment"),
        prepares_for_roles=("financial analyst", "bank manager", "investment analyst"),
    ),
    CollegeProgram(
        major="public administration",
        discipline="public affairs",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("policy analysis", "budgeting", "public management"),
        prepares_for_roles=("city administrator", "agency manager", "policy analyst"),
    ),
    CollegeProgram(
        major="law",
        discipline="legal studies",
        credential_levels=("professional_doctorate",),
        typical_skills=("legal research", "litigation", "statutory analysis"),
        prepares_for_roles=("attorney", "judge", "legal counsel"),
    ),
    CollegeProgram(
        major="criminal justice",
        discipline="public safety",
        credential_levels=("associate", "bachelors", "masters"),
        typical_skills=("case analysis", "public safety policy", "investigation"),
        prepares_for_roles=("police officer", "probation officer", "public safety analyst"),
    ),
    CollegeProgram(
        major="education",
        discipline="education",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("instruction", "curriculum design", "student assessment"),
        prepares_for_roles=("teacher", "school administrator", "curriculum specialist"),
    ),
    CollegeProgram(
        major="nursing",
        discipline="health professions",
        credential_levels=("associate", "bachelors", "masters", "doctorate"),
        typical_skills=("patient care", "clinical assessment", "care coordination"),
        prepares_for_roles=("registered nurse", "nurse practitioner", "nurse manager"),
    ),
    CollegeProgram(
        major="public health",
        discipline="health professions",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("epidemiology", "program evaluation", "health policy"),
        prepares_for_roles=("public health analyst", "health program manager"),
    ),
    CollegeProgram(
        major="computer science",
        discipline="computer and information sciences",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("programming", "algorithms", "software design"),
        prepares_for_roles=("software developer", "systems analyst", "data engineer"),
    ),
    CollegeProgram(
        major="information technology",
        discipline="computer and information sciences",
        credential_levels=("associate", "bachelors", "masters"),
        typical_skills=("network administration", "systems support", "cybersecurity"),
        prepares_for_roles=("IT specialist", "network administrator", "security analyst"),
    ),
    CollegeProgram(
        major="data science",
        discipline="computer and information sciences",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("statistics", "machine learning", "data visualization"),
        prepares_for_roles=("data analyst", "data scientist", "research analyst"),
    ),
    CollegeProgram(
        major="civil engineering",
        discipline="engineering",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("structural analysis", "infrastructure design", "project review"),
        prepares_for_roles=("civil engineer", "public works engineer"),
    ),
    CollegeProgram(
        major="electrical engineering",
        discipline="engineering",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("circuit design", "power systems", "controls"),
        prepares_for_roles=("electrical engineer", "utility engineer"),
    ),
    CollegeProgram(
        major="architecture",
        discipline="architecture",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("building design", "site planning", "construction documents"),
        prepares_for_roles=("architect", "design consultant"),
    ),
    CollegeProgram(
        major="urban planning",
        discipline="architecture and planning",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("zoning analysis", "land use planning", "community engagement"),
        prepares_for_roles=("urban planner", "zoning analyst"),
    ),
    CollegeProgram(
        major="environmental science",
        discipline="natural resources and conservation",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("field sampling", "environmental review", "risk assessment"),
        prepares_for_roles=("environmental scientist", "sustainability analyst"),
    ),
    CollegeProgram(
        major="biology",
        discipline="biological sciences",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("laboratory methods", "research design", "data analysis"),
        prepares_for_roles=("lab technician", "research scientist"),
    ),
    CollegeProgram(
        major="chemistry",
        discipline="physical sciences",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("chemical analysis", "laboratory safety", "quality testing"),
        prepares_for_roles=("chemist", "quality control analyst"),
    ),
    CollegeProgram(
        major="mathematics",
        discipline="mathematics and statistics",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("mathematical modeling", "proof", "quantitative analysis"),
        prepares_for_roles=("quantitative analyst", "teacher", "researcher"),
    ),
    CollegeProgram(
        major="economics",
        discipline="social sciences",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("economic modeling", "forecasting", "policy evaluation"),
        prepares_for_roles=("economist", "policy analyst", "market analyst"),
    ),
    CollegeProgram(
        major="psychology",
        discipline="psychology",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("behavioral assessment", "research methods", "counseling"),
        prepares_for_roles=("counselor", "research assistant", "clinical psychologist"),
    ),
    CollegeProgram(
        major="social work",
        discipline="public and social services",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("case management", "client advocacy", "program coordination"),
        prepares_for_roles=("social worker", "case manager", "program director"),
    ),
    CollegeProgram(
        major="sociology",
        discipline="social sciences",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("survey methods", "community analysis", "qualitative research"),
        prepares_for_roles=("research analyst", "community program analyst"),
    ),
    CollegeProgram(
        major="communications",
        discipline="communication and journalism",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("public speaking", "media writing", "campaign planning"),
        prepares_for_roles=("communications specialist", "public relations manager"),
    ),
    CollegeProgram(
        major="journalism",
        discipline="communication and journalism",
        credential_levels=("bachelors", "masters"),
        typical_skills=("reporting", "editing", "source development"),
        prepares_for_roles=("journalist", "editor", "media producer"),
    ),
    CollegeProgram(
        major="english",
        discipline="english language and literature",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("writing", "editing", "literary analysis"),
        prepares_for_roles=("writer", "editor", "teacher"),
    ),
    CollegeProgram(
        major="history",
        discipline="history",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("archival research", "historical analysis", "writing"),
        prepares_for_roles=("historian", "teacher", "museum curator"),
    ),
    CollegeProgram(
        major="fine arts",
        discipline="visual and performing arts",
        credential_levels=("bachelors", "masters", "doctorate"),
        typical_skills=("studio practice", "design", "critique"),
        prepares_for_roles=("artist", "designer", "arts educator"),
    ),
)


COLLEGE_DISCIPLINE_WEIGHTS_BY_CREDENTIAL: dict[str, dict[str, float]] = {
    "bachelors": {
        "business": 19.0,
        "health professions": 13.0,
        "social sciences": 8.0,
        "computer and information sciences": 6.0,
        "engineering": 6.0,
        "biological sciences": 6.0,
        "psychology": 6.0,
        "communication and journalism": 4.0,
        "education": 4.0,
        "visual and performing arts": 4.0,
        "public safety": 3.0,
        "english language and literature": 2.0,
        "natural resources and conservation": 2.0,
        "mathematics and statistics": 2.0,
        "history": 1.0,
        "architecture": 1.0,
        "architecture and planning": 1.0,
        "physical sciences": 1.0,
        "public affairs": 1.0,
        "public and social services": 1.0,
    },
    "masters": {
        "business": 24.0,
        "education": 18.0,
        "health professions": 16.0,
        "public affairs": 6.0,
        "computer and information sciences": 5.0,
        "engineering": 5.0,
        "public and social services": 5.0,
        "psychology": 4.0,
        "social sciences": 3.0,
        "architecture and planning": 2.0,
        "communication and journalism": 2.0,
        "natural resources and conservation": 1.0,
        "mathematics and statistics": 1.0,
        "visual and performing arts": 1.0,
    },
    "doctorate": {
        "health professions": 38.0,
        "legal studies": 14.0,
        "education": 9.0,
        "engineering": 7.0,
        "biological sciences": 6.0,
        "psychology": 5.0,
        "physical sciences": 3.0,
        "business": 3.0,
        "computer and information sciences": 3.0,
        "social sciences": 3.0,
        "mathematics and statistics": 2.0,
        "public affairs": 1.0,
    },
    "professional_doctorate": {
        "legal studies": 45.0,
        "health professions": 45.0,
        "business": 2.0,
        "education": 2.0,
    },
}


TRADE_SCHOOL_PROGRAMS: tuple[TradeSchoolProgram, ...] = (
    TradeSchoolProgram(
        program="plumbing technology",
        sector="plumbing_services",
        typical_skills=("pipefitting", "water systems", "fixture installation"),
        prepares_for_roles=("plumber", "pipefitter"),
    ),
    TradeSchoolProgram(
        program="HVAC technology",
        sector="hvac_services",
        typical_skills=("heating systems", "air conditioning", "refrigeration"),
        prepares_for_roles=("HVAC technician",),
    ),
    TradeSchoolProgram(
        program="roofing",
        sector="roofing_services",
        typical_skills=("roof repair", "weatherproofing", "fall safety"),
        prepares_for_roles=("roofer",),
    ),
    TradeSchoolProgram(
        program="electrical technology",
        sector="electrical_services",
        typical_skills=("wiring", "power systems", "code compliance"),
        prepares_for_roles=("electrician", "lineworker"),
    ),
    TradeSchoolProgram(
        program="carpentry",
        sector="carpentry_services",
        typical_skills=("framing", "finish carpentry", "blueprint reading"),
        prepares_for_roles=("carpenter",),
    ),
    TradeSchoolProgram(
        program="masonry",
        sector="masonry_services",
        typical_skills=("brickwork", "blockwork", "stone setting"),
        prepares_for_roles=("masonry worker",),
    ),
    TradeSchoolProgram(
        program="welding",
        sector="welding_services",
        typical_skills=("arc welding", "metal fabrication", "safety inspection"),
        prepares_for_roles=("welder",),
    ),
    TradeSchoolProgram(
        program="automotive service technology",
        sector="auto_services",
        typical_skills=("engine repair", "diagnostics", "brake systems"),
        prepares_for_roles=("automotive service technician",),
    ),
    TradeSchoolProgram(
        program="diesel technology",
        sector="diesel_repair",
        typical_skills=("diesel engines", "hydraulics", "fleet maintenance"),
        prepares_for_roles=("diesel mechanic",),
    ),
    TradeSchoolProgram(
        program="heavy equipment maintenance",
        sector="heavy_equipment_repair",
        typical_skills=("hydraulics", "drivetrains", "preventive maintenance"),
        prepares_for_roles=("heavy equipment mechanic",),
    ),
    TradeSchoolProgram(
        program="appliance repair",
        sector="appliance_repair",
        typical_skills=("appliance diagnostics", "electrical repair", "customer service"),
        prepares_for_roles=("appliance repair technician",),
    ),
    TradeSchoolProgram(
        program="security system installation",
        sector="security_systems",
        typical_skills=("low-voltage wiring", "alarm systems", "access control"),
        prepares_for_roles=("security system installer",),
    ),
    TradeSchoolProgram(
        program="building inspection",
        sector="building_inspection",
        typical_skills=("code review", "field inspection", "permit compliance"),
        prepares_for_roles=("building inspector",),
    ),
    TradeSchoolProgram(
        program="drywall installation",
        sector="drywall_services",
        typical_skills=("wallboard installation", "taping", "finishing"),
        prepares_for_roles=("drywall installer",),
    ),
    TradeSchoolProgram(
        program="flooring installation",
        sector="flooring_services",
        typical_skills=("tile setting", "carpet installation", "subfloor preparation"),
        prepares_for_roles=("flooring installer",),
    ),
    TradeSchoolProgram(
        program="solar photovoltaic installation",
        sector="solar_installation",
        typical_skills=("solar panel installation", "roof mounting", "electrical safety"),
        prepares_for_roles=("solar photovoltaic installer",),
    ),
)


PRIVATE_SERVICE_JOBS: tuple[JobTemplate, ...] = (
    JobTemplate(
        role="retail salesperson",
        employment_status="employed",
        income_band="low",
        employer_type="private_business",
        sector="retail",
        serves=("residents",),
        organization_type="business",
    ),
    JobTemplate(
        role="restaurant server",
        employment_status="employed",
        income_band="low",
        employer_type="private_business",
        sector="food_services",
        serves=("residents", "workers"),
        organization_type="business",
    ),
    JobTemplate(
        role="plumber",
        employment_status="employed",
        income_band="middle",
        employer_type="private_business",
        sector="plumbing_services",
        serves=("residents", "businesses"),
        organization_type="business",
        required_education="trade",
        min_experience_years=1,
    ),
    JobTemplate(
        role="HVAC technician",
        employment_status="employed",
        income_band="middle",
        employer_type="private_business",
        sector="hvac_services",
        serves=("residents", "businesses"),
        organization_type="business",
        required_education="trade",
        min_experience_years=1,
    ),
    JobTemplate(
        role="roofer",
        employment_status="employed",
        income_band="middle",
        employer_type="private_business",
        sector="roofing_services",
        serves=("residents", "businesses"),
        organization_type="business",
        required_education="trade",
        min_experience_years=1,
    ),
    JobTemplate(
        role="medical assistant",
        employment_status="employed",
        income_band="middle",
        employer_type="private_business",
        sector="healthcare",
        serves=("residents",),
        organization_type="business",
    ),
    JobTemplate(
        role="bookkeeper",
        employment_status="employed",
        income_band="middle",
        employer_type="private_business",
        sector="professional_services",
        serves=("businesses",),
        organization_type="business",
    ),
)


OWNER_OPERATED_BUSINESSES: tuple[BusinessType, ...] = (
    BusinessType(
        sector="landscaping",
        display_name="landscaping business",
        customer_types=("residents", "businesses", "city_contracts"),
        typical_owner_role="landscaping business owner",
    ),
    BusinessType(
        sector="locksmith",
        display_name="locksmith business",
        customer_types=("residents", "businesses"),
        typical_owner_role="locksmith",
    ),
    BusinessType(
        sector="plumbing_services",
        display_name="plumbing services business",
        customer_types=("residents", "businesses"),
        typical_owner_role="plumbing business owner",
    ),
    BusinessType(
        sector="hvac_services",
        display_name="HVAC services business",
        customer_types=("residents", "businesses"),
        typical_owner_role="HVAC business owner",
    ),
    BusinessType(
        sector="roofing_services",
        display_name="roofing services business",
        customer_types=("residents", "businesses"),
        typical_owner_role="roofing business owner",
    ),
    BusinessType(
        sector="professional_services",
        display_name="business services firm",
        customer_types=("businesses",),
        typical_owner_role="business services owner",
        income_band="high",
    ),
    BusinessType(
        sector="contractor_services",
        display_name="building contractor",
        customer_types=("residents", "businesses", "city_contracts"),
        typical_owner_role="building contractor",
    ),
)


BUSINESS_OWNER_JOBS: tuple[JobTemplate, ...] = tuple(
    JobTemplate(
        role=business.typical_owner_role,
        employment_status="business_owner",
        income_band=business.income_band,
        employer_type="owner_operated_business",
        sector=business.sector,
        serves=business.customer_types,
        organization_type="business",
    )
    for business in OWNER_OPERATED_BUSINESSES
)


JOB_POOLS: dict[str, tuple[JobTemplate, ...]] = {
    "city_service": CITY_SERVICE_JOBS,
    "government": GOVERNMENT_JOBS,
    "private_service": PRIVATE_SERVICE_JOBS,
    "business_owner": BUSINESS_OWNER_JOBS,
}


def job_template_for(pool: str, index: int) -> JobTemplate:
    if pool not in JOB_POOLS:
        choices = ", ".join(sorted(JOB_POOLS))
        raise ValueError(f"unknown job pool {pool!r}; choose one of: {choices}")
    return _pick(JOB_POOLS[pool], index)


def eligible_job_template_for(
    pool: str,
    index: int,
    age: int,
    education: str,
    experience_years: int,
) -> JobTemplate:
    if pool not in JOB_POOLS:
        choices = ", ".join(sorted(JOB_POOLS))
        raise ValueError(f"unknown job pool {pool!r}; choose one of: {choices}")
    jobs = JOB_POOLS[pool]
    for offset in range(len(jobs)):
        job = _pick(jobs, index + offset)
        if is_eligible_for_job(job, age, education, experience_years):
            return job
    raise ValueError(f"no eligible job in {pool!r} for supplied adult profile")


def is_eligible_for_job(
    job: JobTemplate,
    age: int,
    education: str,
    experience_years: int,
) -> bool:
    return (
        age >= job.min_age
        and _education_rank(education) >= _education_rank(job.required_education)
        and experience_years >= job.min_experience_years
    )


def business_type_for(index: int) -> BusinessType:
    return _pick(OWNER_OPERATED_BUSINESSES, index)


def trade_school_program_for(index: int) -> TradeSchoolProgram:
    return _pick(TRADE_SCHOOL_PROGRAMS, index)


def college_program_for(index: int) -> CollegeProgram:
    return _pick(COLLEGE_PROGRAMS, index)


def college_programs_for_credential(credential_level: str) -> tuple[CollegeProgram, ...]:
    return tuple(
        program
        for program in COLLEGE_PROGRAMS
        if credential_level in program.credential_levels
    )


def college_program_weight(program: CollegeProgram, credential_level: str) -> float:
    weights = COLLEGE_DISCIPLINE_WEIGHTS_BY_CREDENTIAL.get(credential_level, {})
    return weights.get(program.discipline, 1.0)


def weighted_college_program_for(
    credential_level: str,
    index: int,
) -> CollegeProgram:
    programs = college_programs_for_credential(credential_level)
    if not programs:
        raise ValueError(f"unknown or unsupported credential level {credential_level!r}")
    weighted: list[CollegeProgram] = []
    for program in sorted(
        programs,
        key=lambda value: college_program_weight(value, credential_level),
        reverse=True,
    ):
        weighted.extend([program] * max(round(college_program_weight(program, credential_level)), 1))
    return _pick(tuple(weighted), index)


def _pick(values: tuple[T, ...], index: int) -> T:
    return values[index % len(values)]


def _education_rank(education: str) -> int:
    ranks = {
        "none": 0,
        "high_school": 1,
        "trade": 2,
        "college": 3,
        "graduate": 4,
    }
    return ranks.get(education, 0)
