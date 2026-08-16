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
class OperatingSchedule:
    schedule_type: str = "unspecified"
    days: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    peak_periods: tuple[str, ...] = ()
    start_hour: float | None = None
    end_hour: float | None = None
    annual_hours: float = 0.0
    daytime_share: float = 0.0
    evening_share: float = 0.0
    overnight_share: float = 0.0
    weekend_share: float = 0.0
    seasonal_peak_load: float = 1.0
    noise_burden: float = 0.0
    disruption_burden: float = 0.0

    @property
    def is_daytime_oriented(self) -> bool:
        return self.daytime_share >= max(self.evening_share, self.overnight_share)

    @property
    def is_overnight_oriented(self) -> bool:
        return self.overnight_share > max(self.daytime_share, self.evening_share)


@dataclass(frozen=True)
class DelayedEffect:
    source: str
    target: str
    amount: float
    delay_turns: int = 0
    duration_turns: int = 1
    decay_rate: float = 0.0
    tags: tuple[str, ...] = ()
    explanation: str = ""

    @property
    def is_active(self) -> bool:
        return self.delay_turns <= 0 and self.duration_turns > 0

    def advance(self) -> DelayedEffect | None:
        if self.delay_turns > 0:
            return DelayedEffect(
                source=self.source,
                target=self.target,
                amount=self.amount,
                delay_turns=self.delay_turns - 1,
                duration_turns=self.duration_turns,
                decay_rate=self.decay_rate,
                tags=self.tags,
                explanation=self.explanation,
            )
        next_duration = self.duration_turns - 1
        if next_duration <= 0:
            return None
        next_amount = self.amount * (1.0 - self.decay_rate)
        return DelayedEffect(
            source=self.source,
            target=self.target,
            amount=next_amount,
            delay_turns=0,
            duration_turns=next_duration,
            decay_rate=self.decay_rate,
            tags=self.tags,
            explanation=self.explanation,
        )


@dataclass
class PressureLedger:
    signals: dict[str, float] = field(default_factory=dict)
    explanations: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def add(self, channel: str, amount: float, explanation: str = "") -> None:
        self.signals[channel] = self.signals.get(channel, 0.0) + amount
        if explanation:
            self.explanations[channel] = self.explanations.get(channel, ()) + (explanation,)

    def get(self, channel: str) -> float:
        return self.signals.get(channel, 0.0)


@dataclass(frozen=True)
class FinancialInstitutionProfile:
    institution_type: str = "unspecified"
    charter: str = "unspecified"
    market_roles: tuple[str, ...] = ()
    participant_roles: tuple[str, ...] = ()
    asset_classes: tuple[str, ...] = ()
    deposit_capacity: float = 0.0
    lending_capacity: float = 0.0
    municipal_finance_capacity: float = 0.0
    household_access_score: float = 50.0
    business_access_score: float = 50.0
    liquidity_score: float = 50.0
    risk_score: float = 50.0


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
    schedule: OperatingSchedule = OperatingSchedule()


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
    schedule: OperatingSchedule = OperatingSchedule()
    services: tuple[EmbeddedService, ...] = ()
    financial_profile: FinancialInstitutionProfile | None = None

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
    pending_effects: tuple[DelayedEffect, ...] = ()

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
    pressure_ledger: PressureLedger = field(default_factory=PressureLedger)

