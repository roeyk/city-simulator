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
