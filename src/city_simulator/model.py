from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Demographics:
    children: float = 18_500
    working_age: float = 62_000
    seniors: float = 19_500
    low_income: float = 34_000
    middle_income: float = 48_000
    high_income: float = 18_000

    @property
    def total(self) -> float:
        return self.children + self.working_age + self.seniors


@dataclass(frozen=True)
class CityMetrics:
    happiness: float = 61.0
    public_sentiment: float = 61.0
    crime: float = 28.0
    growth_rate: float = 0.0
    labor_force: float = 42_000
    employed_residents: float = 39_291
    unemployed_residents: float = 2_709
    jobs_in_city: float = 58_000
    job_vacancies: float = 0.0
    commuters_in: float = 18_709
    commuters_out: float = 0.0
    labor_force_participation_rate: float = 0.677
    unemployment_rate: float = 0.0645
    housing_pressure: float = 0.0
    density_per_square_mile: float = 0.0
    service_coverage: float = 61.0
    sentiment_signals: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class CitySensitivity:
    satisfaction_tax: float = 1.0
    satisfaction_housing: float = 1.0
    labor_access_infrastructure: float = 1.0
    labor_access_education: float = 1.0
    labor_access_income: float = 1.0
    crime_unemployment: float = 1.0
    crime_housing: float = 1.0
    crime_services: float = 1.0
    sentiment_migration: float = 1.0
    sentiment_business: float = 1.0
    sentiment_financial_stress: float = 1.0


@dataclass(frozen=True)
class HousingStock:
    estate_home_units: float = 0.0
    large_lot_single_family_units: float = 0.0
    single_family_units: float = 0.0
    rowhouse_units: float = 0.0
    small_multifamily_units: float = 0.0
    mixed_use_shopfront_units: float = 0.0
    garden_apartment_units: float = 0.0
    midrise_apartment_units: float = 0.0
    highrise_apartment_units: float = 0.0
    subsidized_units: float = 0.0
    senior_housing_units: float = 0.0
    student_housing_units: float = 0.0
    pre_1940_units: float = 0.0
    built_1940_1979_units: float = 0.0
    built_1980_1999_units: float = 0.0
    built_2000_2019_units: float = 0.0
    built_2020_plus_units: float = 0.0

    @property
    def total_units(self) -> float:
        return (
            self.estate_home_units
            + self.large_lot_single_family_units
            + self.single_family_units
            + self.rowhouse_units
            + self.small_multifamily_units
            + self.mixed_use_shopfront_units
            + self.garden_apartment_units
            + self.midrise_apartment_units
            + self.highrise_apartment_units
            + self.subsidized_units
            + self.senior_housing_units
            + self.student_housing_units
        )


@dataclass(frozen=True)
class HousingAssistance:
    section8_vouchers: float = 0.0
    voucher_funding: float = 0.0
    voucher_utilization_rate: float = 0.0
    landlord_acceptance_rate: float = 0.0
    inspection_pass_rate: float = 0.0
    waitlist_households: float = 0.0
    average_rent_gap: float = 0.0
    shelter_beds: float = 0.0
    transitional_housing_units: float = 0.0
    permanent_supportive_housing_units: float = 0.0
    homelessness_prevention_households: float = 0.0

    @property
    def usable_vouchers(self) -> float:
        return (
            self.section8_vouchers
            * self.voucher_utilization_rate
            * self.landlord_acceptance_rate
            * self.inspection_pass_rate
        )

    @property
    def emergency_shelter_capacity(self) -> float:
        return self.shelter_beds + self.transitional_housing_units

    @property
    def long_term_housing_stability_capacity(self) -> float:
        return (
            self.usable_vouchers
            + self.permanent_supportive_housing_units
            + self.homelessness_prevention_households
        )


@dataclass(frozen=True)
class EmbeddedService:
    name: str
    service_type: str
    capacity: float = 0.0
    quality: float = 50.0
    access: float = 50.0
    trust: float = 50.0
    operating_cost: float = 0.0
    staff: float = 0.0
    target_groups: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlaceAsset:
    name: str
    asset_type: str
    neighborhood: str | None = None
    capacity: float = 0.0
    jobs: float = 0.0
    condition: float = 70.0
    access_score: float = 50.0
    service_area: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    services: tuple[EmbeddedService, ...] = ()

    def service_capacity(self, service_type: str | None = None) -> float:
        if service_type is None:
            return sum(service.capacity for service in self.services)
        return sum(
            service.capacity
            for service in self.services
            if service.service_type == service_type
        )


@dataclass(frozen=True)
class Neighborhood:
    name: str
    area_square_miles: float = 0.0
    population: float = 0.0
    housing_units: float = 0.0
    jobs: float = 0.0
    land_use_mix: dict[str, float] = field(default_factory=dict)
    adjacent_neighborhoods: tuple[str, ...] = ()
    adjacent_sectors: tuple[str, ...] = ()
    connectivity: dict[str, float] = field(default_factory=dict)
    environmental_exposure: dict[str, float] = field(default_factory=dict)
    service_access: dict[str, float] = field(default_factory=dict)
    housing_stock: HousingStock = HousingStock()
    housing_assistance: HousingAssistance = HousingAssistance()
    place_assets: tuple[PlaceAsset, ...] = ()

    def service_capacity(self, service_type: str | None = None) -> float:
        return sum(asset.service_capacity(service_type) for asset in self.place_assets)


@dataclass(frozen=True)
class CityState:
    year: int = 0
    population: float = 100_000
    demographics: Demographics = Demographics()
    population_profile: dict[str, dict[str, float]] = field(default_factory=dict)
    cohort_profiles: dict[str, dict[str, dict[str, float]]] = field(default_factory=dict)
    physical_profile: dict[str, dict[str, float] | float] = field(default_factory=dict)
    civic_assets: dict[str, float] = field(default_factory=dict)
    neighborhoods: dict[str, Neighborhood] = field(default_factory=dict)
    place_assets: tuple[PlaceAsset, ...] = ()
    housing_stock: HousingStock = HousingStock()
    housing_assistance: HousingAssistance = HousingAssistance()
    housing_units: float = 43_000
    jobs: float = 58_000
    budget: float = 125_000_000
    infrastructure: float = 72.0
    pollution: float = 38.0
    satisfaction: float = 61.0
    metrics: CityMetrics = CityMetrics()
    sensitivity: CitySensitivity = CitySensitivity()

    def service_capacity(self, service_type: str | None = None) -> float:
        neighborhood_capacity = sum(
            neighborhood.service_capacity(service_type)
            for neighborhood in self.neighborhoods.values()
        )
        citywide_capacity = sum(
            asset.service_capacity(service_type) for asset in self.place_assets
        )
        return neighborhood_capacity + citywide_capacity


@dataclass(frozen=True)
class CityPolicy:
    tax_rate: float = 0.18
    housing_investment: float = 25_000_000
    transit_investment: float = 18_000_000
    services_investment: float = 22_000_000
    environment_investment: float = 8_000_000
    business_support: float = 10_000_000
    citizen_influx_rate: float = 0.006
    citizen_outflux_rate: float = 0.003
    zoning_restrictiveness: float = 0.35
    permitting_speed: float = 0.55
    development_restriction: float = 0.25


@dataclass(frozen=True)
class ExternalControls:
    county_funding: float = 0.0
    county_housing_directive: float = 0.0
    state_funding: float = 0.0
    state_environment_mandate: float = 0.0
    state_service_mandate: float = 0.0
    federal_funding: float = 0.0
    federal_growth_pressure: float = 0.0
    national_interest_rate: float = 0.04
    national_unemployment_pressure: float = 0.0


@dataclass(frozen=True)
class ModelParameters:
    resident_service_cost_per_person: float = 340.0
    financing_cost_budget_share: float = 0.01
    housing_unit_cost: float = 155_000.0
    zoning_housing_drag: float = 0.45
    development_housing_drag: float = 0.35
    permitting_housing_bonus: float = 0.25
    business_support_per_job: float = 30_000.0
    infrastructure_jobs_multiplier: float = 12.0
    high_tax_job_drag_multiplier: float = 5_000.0
    development_job_drag_multiplier: float = 500.0
    national_unemployment_job_drag_multiplier: float = 4_500.0
    infrastructure_annual_wear: float = 2.4
    transit_investment_per_infrastructure_point: float = 11_000_000.0
    services_investment_per_infrastructure_point: float = 35_000_000.0
    pollution_population_divisor: float = 120_000.0
    pollution_jobs_divisor: float = 18_000.0
    environment_spending_per_pollution_point: float = 9_000_000.0
    service_satisfaction_divisor: float = 9.0
    tax_satisfaction_penalty: float = 42.0
    housing_satisfaction_divisor: float = 900.0
    zoning_satisfaction_penalty: float = 3.0
    development_satisfaction_penalty: float = 2.0
    budget_deficit_satisfaction_penalty: float = 8.0
    base_satisfaction: float = 45.0
    infrastructure_satisfaction_bonus: float = 0.22
    pollution_satisfaction_penalty: float = 0.18
    satisfaction_growth_divisor: float = 900.0
    housing_population_drag_divisor: float = 60_000.0
    high_tax_migration_drag: float = 0.035
    zoning_migration_drag: float = 0.0025
    development_migration_drag: float = 0.002
    base_labor_participation: float = 0.66
    high_income_labor_participation_bonus: float = 0.08
    low_income_labor_participation_drag: float = 0.04
    base_job_access: float = 0.72
    infrastructure_job_access_divisor: float = 500.0
    low_income_job_access_drag: float = 0.08
    default_education_mismatch: float = 0.08
    commuter_fill_base: float = 0.22
    commuter_fill_education_bonus: float = 0.9
    base_crime: float = 18.0
    crime_unemployment_multiplier: float = 130.0
    crime_housing_multiplier: float = 180.0
    crime_low_satisfaction_multiplier: float = 0.6
    crime_pollution_multiplier: float = 0.2
    crime_service_mitigation: float = 0.08
    public_sentiment_weights: dict[str, float] = field(
        default_factory=lambda: {
            "survey": 0.24,
            "migration_behavior": 0.11,
            "business_behavior": 0.1,
            "consumer_spending": 0.1,
            "savings_security": 0.09,
            "housing_stress": 0.1,
            "safety": 0.08,
            "services": 0.07,
            "civic_trust": 0.07,
            "future_confidence": 0.04,
        }
    )


@dataclass(frozen=True)
class Issue:
    code: str
    name: str
    severity: str
    detail: str


@dataclass(frozen=True)
class YearResult:
    year: int
    state: CityState
    revenue: float
    expenses: float
    population_delta: float
    jobs_delta: float
    housing_gap: float
    active_issues: list[Issue]
    overcome_issues: list[Issue]


def simulate(
    initial_state: CityState,
    policy: CityPolicy,
    years: int,
    external: ExternalControls | None = None,
    parameters: ModelParameters | None = None,
) -> list[YearResult]:
    if years < 0:
        raise ValueError("years must be non-negative")

    state = initial_state
    results: list[YearResult] = []
    external_controls = external or ExternalControls()
    model_parameters = parameters or ModelParameters()
    for _ in range(years):
        result = advance_year(state, policy, external_controls, model_parameters)
        results.append(result)
        state = result.state
    return results


def advance_year(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls | None = None,
    parameters: ModelParameters | None = None,
) -> YearResult:
    _validate_policy(policy)
    external_controls = external or ExternalControls()
    model_parameters = parameters or ModelParameters()
    previous_issues = detect_issues(state, model_parameters)

    intergovernmental_funding = (
        external_controls.county_funding
        + external_controls.state_funding
        + external_controls.federal_funding
    )
    revenue = _tax_base(state) * policy.tax_rate + intergovernmental_funding
    financing_cost = (
        max(state.budget, 0.0)
        * max(external_controls.national_interest_rate, 0.0)
        * model_parameters.financing_cost_budget_share
    )
    expenses = (
        policy.housing_investment
        + policy.transit_investment
        + policy.services_investment
        + policy.environment_investment
        + policy.business_support
        + state.population * model_parameters.resident_service_cost_per_person
        + financing_cost
    )
    budget = state.budget + revenue - expenses

    housing_units = state.housing_units + _housing_units_added(
        policy,
        external_controls,
        model_parameters,
        state.sensitivity,
    )
    jobs_delta = _jobs_delta(state, policy, external_controls, model_parameters)
    jobs = max(0.0, state.jobs + jobs_delta)

    infrastructure = _clamp(
        state.infrastructure
        - model_parameters.infrastructure_annual_wear
        + policy.transit_investment
        / model_parameters.transit_investment_per_infrastructure_point
        + policy.services_investment
        / model_parameters.services_investment_per_infrastructure_point,
        0.0,
        100.0,
    )
    pollution = _clamp(
        state.pollution
        + state.population / model_parameters.pollution_population_divisor
        + max(jobs_delta, 0.0) / model_parameters.pollution_jobs_divisor
        - (policy.environment_investment + external_controls.state_environment_mandate)
        / model_parameters.environment_spending_per_pollution_point,
        0.0,
        100.0,
    )

    housing_gap = state.population / 2.35 - housing_units
    satisfaction = _satisfaction(
        state,
        policy,
        external_controls,
        infrastructure,
        pollution,
        housing_gap,
        model_parameters,
        state.sensitivity,
    )
    population_delta = _population_delta(
        state,
        policy,
        satisfaction,
        housing_gap,
        external_controls,
        model_parameters,
    )
    population = max(0.0, state.population + population_delta)
    demographics = _advance_demographics(state, policy, population, population_delta)
    growth_rate = population_delta / max(state.population, 1.0)

    next_state = CityState(
        year=state.year + 1,
        population=population,
        demographics=demographics,
        population_profile=state.population_profile,
        cohort_profiles=state.cohort_profiles,
        physical_profile=state.physical_profile,
        civic_assets=state.civic_assets,
        neighborhoods=state.neighborhoods,
        housing_stock=state.housing_stock,
        housing_assistance=state.housing_assistance,
        housing_units=housing_units,
        jobs=jobs,
        budget=budget,
        infrastructure=infrastructure,
        pollution=pollution,
        satisfaction=satisfaction,
        metrics=_city_metrics(
            state=state,
            population=population,
            demographics=demographics,
            jobs=jobs,
            jobs_delta=jobs_delta,
            housing_units=housing_units,
            housing_gap=housing_gap,
            satisfaction=satisfaction,
            infrastructure=infrastructure,
            pollution=pollution,
            growth_rate=growth_rate,
            parameters=model_parameters,
            sensitivity=state.sensitivity,
        ),
        sensitivity=state.sensitivity,
    )
    active_issues = detect_issues(next_state, model_parameters)
    return YearResult(
        year=next_state.year,
        state=next_state,
        revenue=revenue,
        expenses=expenses,
        population_delta=population_delta,
        jobs_delta=jobs_delta,
        housing_gap=housing_gap,
        active_issues=active_issues,
        overcome_issues=_overcome_issues(previous_issues, active_issues),
    )


def detect_issues(
    state: CityState,
    parameters: ModelParameters | None = None,
) -> list[Issue]:
    model_parameters = parameters or ModelParameters()
    issues: list[Issue] = []
    housing_gap = state.population / 2.35 - state.housing_units
    labor = _labor_market(
        population=state.population,
        demographics=state.demographics,
        jobs=state.jobs,
        infrastructure=state.infrastructure,
        education_profile=state.population_profile.get("education_percent", {}),
        parameters=model_parameters,
        sensitivity=state.sensitivity,
    )
    unemployment_rate = labor["unemployment_rate"]
    if housing_gap > state.population * 0.025:
        issues.append(
            Issue(
                code="housing_shortage",
                name="housing shortage",
                severity="high" if housing_gap > state.population * 0.05 else "medium",
                detail=f"{housing_gap:,.0f} more homes are needed.",
            )
        )
    if unemployment_rate > 0.08:
        issues.append(
            Issue(
                code="unemployment",
                name="unemployment",
                severity="high" if unemployment_rate > 0.13 else "medium",
                detail=f"{unemployment_rate:.1%} of the labor force is unemployed.",
            )
        )
    if state.budget < 0:
        issues.append(
            Issue(
                code="budget_deficit",
                name="budget deficit",
                severity="high",
                detail=f"The city is ${abs(state.budget):,.0f} below balance.",
            )
        )
    if state.infrastructure < 55:
        issues.append(
            Issue(
                code="aging_infrastructure",
                name="aging infrastructure",
                severity="high" if state.infrastructure < 40 else "medium",
                detail=f"Infrastructure condition is {state.infrastructure:.1f}/100.",
            )
        )
    if state.pollution > 58:
        issues.append(
            Issue(
                code="pollution",
                name="pollution",
                severity="high" if state.pollution > 72 else "medium",
                detail=f"Pollution is {state.pollution:.1f}/100.",
            )
        )
    if state.satisfaction < 45:
        issues.append(
            Issue(
                code="low_satisfaction",
                name="low satisfaction",
                severity="high" if state.satisfaction < 35 else "medium",
                detail=f"Resident satisfaction is {state.satisfaction:.1f}/100.",
            )
        )
    if state.demographics.low_income / max(state.population, 1.0) > 0.42:
        issues.append(
            Issue(
                code="income_stress",
                name="income stress",
                severity="medium",
                detail="More than 42% of residents are low income.",
            )
        )
    return issues


def _validate_policy(policy: CityPolicy) -> None:
    if not 0.0 <= policy.tax_rate <= 1.0:
        raise ValueError("tax_rate must be between 0.0 and 1.0")
    rates = {
        "citizen_influx_rate": policy.citizen_influx_rate,
        "citizen_outflux_rate": policy.citizen_outflux_rate,
    }
    for name, value in rates.items():
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    bounded = {
        "zoning_restrictiveness": policy.zoning_restrictiveness,
        "permitting_speed": policy.permitting_speed,
        "development_restriction": policy.development_restriction,
    }
    for name, value in bounded.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0.0 and 1.0")
    investments = (
        policy.housing_investment,
        policy.transit_investment,
        policy.services_investment,
        policy.environment_investment,
        policy.business_support,
    )
    if any(value < 0 for value in investments):
        raise ValueError("investments must be non-negative")


def _housing_units_added(
    policy: CityPolicy,
    external: ExternalControls,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> float:
    buildable_share = _clamp(
        1.0
        - policy.zoning_restrictiveness
        * parameters.zoning_housing_drag
        * sensitivity.satisfaction_housing
        - policy.development_restriction * parameters.development_housing_drag
        + policy.permitting_speed * parameters.permitting_housing_bonus,
        0.15,
        1.25,
    )
    return (
        policy.housing_investment + external.county_housing_directive
    ) / parameters.housing_unit_cost * buildable_share


def _tax_base(state: CityState) -> float:
    income_base = (
        state.demographics.low_income * 16_000
        + state.demographics.middle_income * 34_000
        + state.demographics.high_income * 72_000
    )
    return income_base + state.jobs * 19_000


def _jobs_delta(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls,
    parameters: ModelParameters,
) -> float:
    business_effect = policy.business_support / parameters.business_support_per_job
    infrastructure_effect = (
        state.infrastructure - 50.0
    ) * parameters.infrastructure_jobs_multiplier
    tax_drag = max(policy.tax_rate - 0.2, 0.0) * parameters.high_tax_job_drag_multiplier
    restriction_drag = (
        policy.development_restriction * parameters.development_job_drag_multiplier
    )
    national_drag = (
        external.national_unemployment_pressure
        * parameters.national_unemployment_job_drag_multiplier
    )
    return business_effect + infrastructure_effect - tax_drag - restriction_drag - national_drag


def _advance_demographics(
    state: CityState,
    policy: CityPolicy,
    population: float,
    population_delta: float,
) -> Demographics:
    previous = state.demographics
    children = previous.children * 0.965 + max(population_delta, 0.0) * 0.18
    seniors = previous.seniors * 1.025 + previous.working_age * 0.012
    working_age = max(population - children - seniors, 0.0)

    upward_mobility = (
        policy.business_support / 150_000_000
        + policy.services_investment / 220_000_000
    )
    tax_pressure = max(policy.tax_rate - 0.2, 0.0) * 0.08
    low_share = _clamp(
        previous.low_income / max(previous.total, 1.0) - upward_mobility * 0.02 + tax_pressure,
        0.18,
        0.55,
    )
    high_share = _clamp(
        previous.high_income / max(previous.total, 1.0)
        + upward_mobility * 0.012
        - tax_pressure * 0.35,
        0.08,
        0.32,
    )
    middle_share = max(0.0, 1.0 - low_share - high_share)
    return Demographics(
        children=children,
        working_age=working_age,
        seniors=seniors,
        low_income=population * low_share,
        middle_income=population * middle_share,
        high_income=population * high_share,
    )


def _satisfaction(
    state: CityState,
    policy: CityPolicy,
    external: ExternalControls,
    infrastructure: float,
    pollution: float,
    housing_gap: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> float:
    service_score = (
        policy.services_investment + external.state_service_mandate
    ) / max(state.population, 1.0) / parameters.service_satisfaction_divisor
    tax_penalty = (
        policy.tax_rate * parameters.tax_satisfaction_penalty * sensitivity.satisfaction_tax
    )
    housing_penalty = (
        max(housing_gap, 0.0)
        / parameters.housing_satisfaction_divisor
        * sensitivity.satisfaction_housing
    )
    restriction_penalty = (
        policy.zoning_restrictiveness * parameters.zoning_satisfaction_penalty
        + policy.development_restriction * parameters.development_satisfaction_penalty
    )
    budget_penalty = parameters.budget_deficit_satisfaction_penalty if state.budget < 0 else 0.0
    raw = (
        parameters.base_satisfaction
        + infrastructure * parameters.infrastructure_satisfaction_bonus
        + service_score
        - pollution * parameters.pollution_satisfaction_penalty
    )
    return _clamp(
        raw - tax_penalty - housing_penalty - restriction_penalty - budget_penalty,
        0.0,
        100.0,
    )


def _population_delta(
    state: CityState,
    policy: CityPolicy,
    satisfaction: float,
    housing_gap: float,
    external: ExternalControls,
    parameters: ModelParameters,
) -> float:
    growth_rate = (
        satisfaction - parameters.base_satisfaction
    ) / parameters.satisfaction_growth_divisor
    housing_drag = max(housing_gap, 0.0) / parameters.housing_population_drag_divisor
    migration_rate = policy.citizen_influx_rate - policy.citizen_outflux_rate
    tax_migration_drag = max(policy.tax_rate - 0.22, 0.0) * parameters.high_tax_migration_drag
    restriction_drag = (
        policy.zoning_restrictiveness * parameters.zoning_migration_drag
        + policy.development_restriction * parameters.development_migration_drag
    )
    return state.population * (
        growth_rate
        - housing_drag
        + migration_rate
        + external.federal_growth_pressure
        - tax_migration_drag
        - restriction_drag
    )


def _city_metrics(
    state: CityState,
    population: float,
    demographics: Demographics,
    jobs: float,
    jobs_delta: float,
    housing_units: float,
    housing_gap: float,
    satisfaction: float,
    infrastructure: float,
    pollution: float,
    growth_rate: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> CityMetrics:
    service_coverage = _service_coverage(state)
    labor = _labor_market(
        population=population,
        demographics=demographics,
        jobs=jobs,
        infrastructure=infrastructure,
        education_profile=state.population_profile.get("education_percent", {}),
        parameters=parameters,
        sensitivity=sensitivity,
    )
    unemployment_rate = labor["unemployment_rate"]
    housing_pressure = max(housing_gap, 0.0) / max(population, 1.0)
    density = _density(population, state)
    crime = _clamp(
        parameters.base_crime
        + unemployment_rate
        * parameters.crime_unemployment_multiplier
        * sensitivity.crime_unemployment
        + housing_pressure * parameters.crime_housing_multiplier * sensitivity.crime_housing
        + max(50.0 - satisfaction, 0.0) * parameters.crime_low_satisfaction_multiplier
        + max(pollution - 55.0, 0.0) * parameters.crime_pollution_multiplier
        - service_coverage * parameters.crime_service_mitigation * sensitivity.crime_services,
        0.0,
        100.0,
    )
    sentiment_signals = _sentiment_signals(
        state=state,
        demographics=demographics,
        satisfaction=satisfaction,
        growth_rate=growth_rate,
        jobs_delta=jobs_delta,
        pollution=pollution,
        unemployment_rate=unemployment_rate,
        job_vacancy_rate=labor["job_vacancy_rate"],
        crime=crime,
        housing_pressure=housing_pressure,
        service_coverage=service_coverage,
        parameters=parameters,
        sensitivity=sensitivity,
    )
    return CityMetrics(
        happiness=satisfaction,
        public_sentiment=_public_sentiment(sentiment_signals, parameters),
        crime=crime,
        growth_rate=growth_rate,
        labor_force=labor["labor_force"],
        employed_residents=labor["employed_residents"],
        unemployed_residents=labor["unemployed_residents"],
        jobs_in_city=jobs,
        job_vacancies=labor["job_vacancies"],
        commuters_in=labor["commuters_in"],
        commuters_out=labor["commuters_out"],
        labor_force_participation_rate=labor["labor_force_participation_rate"],
        unemployment_rate=unemployment_rate,
        housing_pressure=housing_pressure,
        density_per_square_mile=density,
        service_coverage=service_coverage,
        sentiment_signals=sentiment_signals,
    )


def _labor_market(
    population: float,
    demographics: Demographics,
    jobs: float,
    infrastructure: float,
    education_profile: dict[str, float],
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> dict[str, float]:
    high_income_share = demographics.high_income / max(population, 1.0)
    low_income_share = demographics.low_income / max(population, 1.0)
    education_drag = _education_mismatch(education_profile, parameters)
    participation_rate = _clamp(
        parameters.base_labor_participation
        + high_income_share * parameters.high_income_labor_participation_bonus
        - low_income_share * parameters.low_income_labor_participation_drag,
        0.52,
        0.78,
    )
    labor_force = demographics.working_age * participation_rate
    access_score = _clamp(
        parameters.base_job_access
        + infrastructure
        / parameters.infrastructure_job_access_divisor
        * sensitivity.labor_access_infrastructure
        - education_drag * sensitivity.labor_access_education
        - low_income_share
        * parameters.low_income_job_access_drag
        * sensitivity.labor_access_income,
        0.42,
        0.94,
    )
    resident_accessible_jobs = jobs * access_score
    employed_residents = min(labor_force, resident_accessible_jobs)
    unemployed_residents = max(labor_force - employed_residents, 0.0)
    remaining_city_jobs = max(jobs - employed_residents, 0.0)
    commuter_fill_rate = _clamp(
        parameters.commuter_fill_base
        + education_drag * parameters.commuter_fill_education_bonus,
        0.12,
        0.55,
    )
    commuters_in = min(remaining_city_jobs, jobs * commuter_fill_rate)
    job_vacancies = max(remaining_city_jobs - commuters_in, 0.0)
    commuters_out = max(employed_residents - jobs, 0.0)
    return {
        "labor_force": labor_force,
        "employed_residents": employed_residents,
        "unemployed_residents": unemployed_residents,
        "jobs_in_city": jobs,
        "job_vacancies": job_vacancies,
        "commuters_in": commuters_in,
        "commuters_out": commuters_out,
        "labor_force_participation_rate": participation_rate,
        "unemployment_rate": unemployed_residents / max(labor_force, 1.0),
        "job_vacancy_rate": job_vacancies / max(jobs, 1.0),
    }


def _education_mismatch(
    education_profile: dict[str, float],
    parameters: ModelParameters | None = None,
) -> float:
    model_parameters = parameters or ModelParameters()
    if not education_profile:
        return model_parameters.default_education_mismatch
    less_than_high_school = education_profile.get("less_than_high_school", 0.0)
    high_school = education_profile.get("high_school", 0.0)
    college_or_higher = (
        education_profile.get("bachelors", 0.0)
        + education_profile.get("graduate", 0.0)
        + education_profile.get("college_or_higher", 0.0)
    )
    return _clamp(
        less_than_high_school / 180
        + high_school / 450
        - college_or_higher / 700,
        0.02,
        0.18,
    )


def _density(population: float, state: CityState) -> float:
    area = state.physical_profile.get("area_square_miles") if state.physical_profile else None
    if not isinstance(area, int | float) or area <= 0:
        return 0.0
    return population / area


def _service_coverage(state: CityState) -> float:
    if not state.civic_assets:
        return state.satisfaction
    population_units = max(state.population / 100_000, 0.1)
    schools = state.civic_assets.get("schools", 0.0) / population_units / 42
    fire = state.civic_assets.get("fire_stations", 0.0) / population_units / 12
    police = state.civic_assets.get("police_stations", 0.0) / population_units / 7
    libraries = state.civic_assets.get("libraries", 0.0) / population_units / 9
    return _clamp((schools + fire + police + libraries) / 4 * 100, 0.0, 100.0)


def _sentiment_signals(
    state: CityState,
    demographics: Demographics,
    satisfaction: float,
    growth_rate: float,
    jobs_delta: float,
    pollution: float,
    unemployment_rate: float,
    job_vacancy_rate: float,
    crime: float,
    housing_pressure: float,
    service_coverage: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> dict[str, float]:
    current_population = max(demographics.total, 1.0)
    low_income_share = demographics.low_income / current_population
    high_income_share = demographics.high_income / current_population
    budget_stability = (
        100.0
        if state.budget >= 0
        else _clamp(70.0 + state.budget / 2_000_000, 0.0, 70.0)
    )
    return {
        "survey": satisfaction,
        "migration_behavior": _clamp(
            50.0 + growth_rate * 1_200 * sensitivity.sentiment_migration,
            0.0,
            100.0,
        ),
        "business_behavior": _clamp(
            54.0
            + jobs_delta / 250 * sensitivity.sentiment_business
            - unemployment_rate * 85
            - job_vacancy_rate * 35,
            0.0,
            100.0,
        ),
        "consumer_spending": _clamp(
            45.0
            + satisfaction * 0.35
            - unemployment_rate * 90 * sensitivity.sentiment_financial_stress
            - housing_pressure * 120,
            0.0,
            100.0,
        ),
        "savings_security": _clamp(
            72.0
            - low_income_share * 35 * sensitivity.sentiment_financial_stress
            + high_income_share * 12
            - unemployment_rate * 120 * sensitivity.sentiment_financial_stress,
            0.0,
            100.0,
        ),
        "housing_stress": _clamp(100.0 - housing_pressure * 520, 0.0, 100.0),
        "safety": _clamp(100.0 - crime, 0.0, 100.0),
        "services": service_coverage,
        "civic_trust": _clamp(
            satisfaction * 0.35
            + service_coverage * 0.3
            + budget_stability * 0.2
            + (100.0 - crime) * 0.15,
            0.0,
            100.0,
        ),
        "future_confidence": _clamp(
            52.0 + growth_rate * 800 + jobs_delta / 280 - unemployment_rate * 95 - pollution * 0.12,
            0.0,
            100.0,
        ),
    }


def _public_sentiment(signals: dict[str, float], parameters: ModelParameters) -> float:
    weights = parameters.public_sentiment_weights
    return sum(signals[key] * weight for key, weight in weights.items())


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _overcome_issues(previous: list[Issue], current: list[Issue]) -> list[Issue]:
    current_codes = {issue.code for issue in current}
    return [issue for issue in previous if issue.code not in current_codes]
