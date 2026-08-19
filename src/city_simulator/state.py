from __future__ import annotations

from dataclasses import dataclass, field

from city_simulator.agents import HouseholdAgent, OrganizationAgent, PersonAgent


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
class CityRevenueSources:
    resident_taxes: float = 0.0
    business_taxes: float = 0.0
    state_grants: float = 0.0
    state_shared_revenue: float = 0.0
    federal_grants: float = 0.0
    fees_and_fines: float = 0.0
    service_charges: float = 0.0
    other: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.resident_taxes
            + self.business_taxes
            + self.state_grants
            + self.state_shared_revenue
            + self.federal_grants
            + self.fees_and_fines
            + self.service_charges
            + self.other
        )


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
class ZoningEnvelope:
    allowed_uses: tuple[str, ...] = ("residential",)
    overlay_tags: tuple[str, ...] = ()
    special_permit_uses: tuple[str, ...] = ()
    max_housing_units: float = 0.0
    max_commercial_jobs: float = 0.0
    max_industrial_jobs: float = 0.0
    max_civic_capacity: float = 0.0
    max_density_per_square_mile: float = 0.0
    max_floor_area_ratio: float = 0.0
    max_height_stories: float = 0.0
    max_lot_coverage: float = 0.0
    parking_spaces_per_home: float = 0.0
    inclusionary_housing_share: float = 0.0
    affordable_housing_bonus: float = 0.0
    historic_preservation_score: float = 0.0
    environmental_constraint_score: float = 0.0
    transit_oriented_development_score: float = 0.0
    redevelopment_priority: float = 0.0
    industrial_protection_score: float = 0.0


@dataclass(frozen=True)
class ParcelGrid:
    grid_type: str = "square"
    width: int = 1000
    height: int = 1000
    cell_size_meters: float = 20.0
    origin_label: str = ""
    commute_minutes_per_grid_step: float = 2.5
    shipping_cost_per_grid_step: float = 1.25

    @property
    def coordinate_capacity(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class ParcelOccupancy:
    person_ids: tuple[str, ...] = ()
    household_ids: tuple[str, ...] = ()
    organization_ids: tuple[str, ...] = ()
    place_asset_ids: tuple[str, ...] = ()
    infrastructure_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Parcel:
    parcel_id: str
    grid_x: int
    grid_y: int
    neighborhood: str = ""
    area_acres: float = 0.0
    land_use: str = "unspecified"
    natural_cover: str = "unknown"
    development_stage: str = "unknown"
    reserved: bool = False
    reserved_for: str = ""
    zoning: ZoningEnvelope = ZoningEnvelope()
    owner_type: str = "unknown"
    owner_id: str = ""
    housing_units: float = 0.0
    max_housing_units: float = 0.0
    jobs: float = 0.0
    max_jobs: float = 0.0
    assessed_value: float = 0.0
    vacancy_rate: float = 0.0
    underused: bool = False
    impervious_surface_share: float = 0.0
    tree_canopy_share: float = 0.0
    stormwater_retention: float = 0.0
    overlays: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    occupancy: ParcelOccupancy = ParcelOccupancy()

    @property
    def coordinate(self) -> tuple[int, int]:
        return (self.grid_x, self.grid_y)


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
class SignalLedger:
    signals: dict[str, float] = field(default_factory=dict)
    explanations: dict[str, tuple[str, ...]] = field(default_factory=dict)
    driver_categories: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def add(
        self,
        channel: str,
        amount: float,
        explanation: str = "",
        driver_categories: tuple[str, ...] = (),
    ) -> None:
        self.signals[channel] = self.signals.get(channel, 0.0) + amount
        if explanation:
            self.explanations[channel] = self.explanations.get(channel, ()) + (explanation,)
        if driver_categories:
            existing = self.driver_categories.get(channel, ())
            self.driver_categories[channel] = existing + tuple(
                category for category in driver_categories if category not in existing
            )

    def get(self, channel: str) -> float:
        return self.signals.get(channel, 0.0)

    def drivers_for(self, channel: str) -> tuple[str, ...]:
        return self.driver_categories.get(channel, ())


@dataclass(frozen=True)
class SectorMarketBalance:
    sector: str
    good_or_service: str
    local_demand: float = 0.0
    local_supply: float = 0.0
    imports: float = 0.0
    exports: float = 0.0
    inventory_or_capacity_drawdown: float = 0.0
    substitution: float = 0.0
    unmet_demand: float = 0.0
    price_pressure: float = 0.0
    wait_pressure: float = 0.0
    utilization: float = 0.0
    notes: tuple[str, ...] = ()

    @property
    def accounted_supply(self) -> float:
        return (
            self.local_supply
            + self.imports
            + self.inventory_or_capacity_drawdown
            + self.substitution
            - self.exports
        )

    @property
    def local_supply_gap(self) -> float:
        return max(self.local_demand - self.local_supply, 0.0)

    @property
    def computed_unmet_demand(self) -> float:
        return max(self.local_demand - self.accounted_supply, 0.0)

    @property
    def effective_unmet_demand(self) -> float:
        return max(self.unmet_demand, self.computed_unmet_demand)

    @property
    def import_share(self) -> float:
        if self.local_demand <= 0:
            return 0.0
        return self.imports / self.local_demand


@dataclass(frozen=True)
class InventoryState:
    holder_type: str
    holder_id: str
    sector: str
    good: str
    quantity: float = 0.0
    daily_use: float = 0.0
    days_on_hand: float = 0.0
    reorder_threshold_days: float = 0.0
    reserve_target_days: float = 0.0
    storage_type: str = "standard"
    spoilage_risk: float = 0.0
    stockout_risk: float = 0.0
    notes: tuple[str, ...] = ()

    @property
    def computed_days_on_hand(self) -> float:
        if self.daily_use <= 0:
            return self.days_on_hand
        return self.quantity / self.daily_use

    @property
    def raw_days_on_hand(self) -> float:
        if self.days_on_hand > 0:
            return self.days_on_hand
        return self.computed_days_on_hand

    @property
    def spoilage_adjustment(self) -> float:
        return max(0.0, min(self.spoilage_risk, 1.0))

    @property
    def effective_days_on_hand(self) -> float:
        return self.raw_days_on_hand * (1.0 - self.spoilage_adjustment)

    @property
    def reorder_gap_days(self) -> float:
        return max(self.reorder_threshold_days - self.effective_days_on_hand, 0.0)

    @property
    def reserve_gap_days(self) -> float:
        return max(self.reserve_target_days - self.effective_days_on_hand, 0.0)

    @property
    def effective_stockout_risk(self) -> float:
        if self.stockout_risk > 0:
            return self.stockout_risk
        if self.reorder_threshold_days <= 0:
            return 0.0
        return min(self.reorder_gap_days / self.reorder_threshold_days, 1.0)

    @property
    def cold_chain_dependent(self) -> bool:
        return self.storage_type in {"cold_chain", "refrigerated", "frozen"}


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
    parcel_id: str = ""
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
    parcel_ids: tuple[str, ...] = ()
    housing_stock: HousingStock = HousingStock()
    housing_assistance: HousingAssistance = HousingAssistance()
    zoning: ZoningEnvelope = ZoningEnvelope()
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
    parcel_grid: ParcelGrid = ParcelGrid()
    parcels: dict[str, Parcel] = field(default_factory=dict)
    place_assets: tuple[PlaceAsset, ...] = ()
    people: tuple[PersonAgent, ...] = ()
    households: tuple[HouseholdAgent, ...] = ()
    organizations: tuple[OrganizationAgent, ...] = ()
    sector_market_balances: tuple[SectorMarketBalance, ...] = ()
    inventories: tuple[InventoryState, ...] = ()
    housing_stock: HousingStock = HousingStock()
    housing_assistance: HousingAssistance = HousingAssistance()
    housing_units: float = 43_000
    jobs: float = 58_000
    budget: float = 125_000_000
    annual_income: float = 0.0
    annual_budget: float = 0.0
    revenue_sources: CityRevenueSources = CityRevenueSources()
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
    business_tax_rate: float = 0.10
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
    infrastructure_pressure_threshold: float = 65.0
    infrastructure_resident_burden_multiplier: float = 0.28
    infrastructure_service_disruption_multiplier: float = 0.36
    infrastructure_organization_disruption_multiplier: float = 0.32
    housing_pressure_threshold: float = 0.015
    housing_build_pressure_multiplier: float = 420.0
    housing_land_constraint_multiplier: float = 520.0
    housing_business_pressure_multiplier: float = 180.0
    pollution_population_divisor: float = 120_000.0
    pollution_jobs_divisor: float = 18_000.0
    environment_spending_per_pollution_point: float = 9_000_000.0
    service_satisfaction_divisor: float = 9.0
    tax_satisfaction_penalty: float = 42.0
    housing_satisfaction_divisor: float = 900.0
    zoning_satisfaction_penalty: float = 3.0
    development_satisfaction_penalty: float = 2.0
    budget_deficit_satisfaction_penalty: float = 8.0
    fiscal_stress_satisfaction_penalty: float = 0.45
    unemployment_migration_drag: float = 0.028
    unemployment_household_buffer: float = 0.45
    job_growth_migration_bonus: float = 0.18
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
    signal_ledger: SignalLedger = field(default_factory=SignalLedger)
