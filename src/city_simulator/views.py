from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, TypeVar

from city_simulator.agents import OrganizationAgent, PersonAgent, ServiceLanguage
from city_simulator.parcels import parcel_grid_distance
from city_simulator.state import CityState, InventoryState, Parcel

ViewT = TypeVar("ViewT", bound="View")


@dataclass(frozen=True)
class View(ABC):
    name: ClassVar[str] = "view"
    source_dependencies: ClassVar[tuple[str, ...]] = ()

    @classmethod
    @abstractmethod
    def derive(cls: type[ViewT], state: CityState) -> ViewT:
        raise NotImplementedError

    @abstractmethod
    def as_dict(self) -> dict[str, float]:
        raise NotImplementedError


@dataclass(frozen=True)
class PopulationStructureView(View):
    name: ClassVar[str] = "population_structure"
    source_dependencies: ClassVar[tuple[str, ...]] = ("population", "demographics")

    total_population: float
    child_share: float
    working_age_share: float
    senior_share: float
    low_income_share: float
    middle_income_share: float
    high_income_share: float
    dependency_ratio: float

    @classmethod
    def derive(cls, state: CityState) -> PopulationStructureView:
        population = max(state.population, 1.0)
        demographics = state.demographics
        dependents = demographics.children + demographics.seniors
        return cls(
            total_population=state.population,
            child_share=demographics.children / population,
            working_age_share=demographics.working_age / population,
            senior_share=demographics.seniors / population,
            low_income_share=demographics.low_income / population,
            middle_income_share=demographics.middle_income / population,
            high_income_share=demographics.high_income / population,
            dependency_ratio=dependents / max(demographics.working_age, 1.0),
        )

    @classmethod
    def derive_from_people(cls, people: tuple[PersonAgent, ...]) -> PopulationStructureView:
        total_population = sum(person.weight for person in people)
        population = max(total_population, 1.0)
        children = sum(person.weight for person in people if person.is_child)
        working_age = sum(person.weight for person in people if person.is_working_age)
        seniors = sum(person.weight for person in people if person.is_senior)
        low_income = sum(person.weight for person in people if person.income_band == "low")
        middle_income = sum(person.weight for person in people if person.income_band == "middle")
        high_income = sum(person.weight for person in people if person.income_band == "high")
        return cls(
            total_population=total_population,
            child_share=children / population,
            working_age_share=working_age / population,
            senior_share=seniors / population,
            low_income_share=low_income / population,
            middle_income_share=middle_income / population,
            high_income_share=high_income / population,
            dependency_ratio=(children + seniors) / max(working_age, 1.0),
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "total_population": self.total_population,
            "child_share": self.child_share,
            "working_age_share": self.working_age_share,
            "senior_share": self.senior_share,
            "low_income_share": self.low_income_share,
            "middle_income_share": self.middle_income_share,
            "high_income_share": self.high_income_share,
            "dependency_ratio": self.dependency_ratio,
        }


def language_service_access_score(
    person: PersonAgent,
    organization: OrganizationAgent,
) -> float:
    if not organization.service_languages:
        return 50.0
    return max(
        _service_language_access_score(person, service_language)
        for service_language in organization.service_languages
    )


def _service_language_access_score(
    person: PersonAgent,
    service_language: ServiceLanguage,
) -> float:
    person_rank = person.language_profile.spoken_rank(service_language.language)
    direct_score = min(person_rank, service_language.service_rank) / 4 * 100
    if (
        person.language_profile.interpreter_needed
        and service_language.interpreter_capacity > 0
        and person_rank > 0
    ):
        return max(direct_score, 70.0)
    return direct_score


@dataclass(frozen=True)
class LanguageAccessView(View):
    name: ClassVar[str] = "language_access"
    source_dependencies: ClassVar[tuple[str, ...]] = ("people", "organizations")

    total_people_weight: float
    organizations_with_service_languages: float
    average_service_access_score: float
    limited_access_share: float
    interpreter_need_share: float
    multilingual_bridge_share: float

    @classmethod
    def derive(cls, state: CityState) -> LanguageAccessView:
        return cls.derive_from_agents(state.people, state.organizations)

    @classmethod
    def derive_from_agents(
        cls,
        people: tuple[PersonAgent, ...],
        organizations: tuple[OrganizationAgent, ...],
    ) -> LanguageAccessView:
        total_weight = sum(person.weight for person in people)
        population = max(total_weight, 1.0)
        service_organizations = tuple(
            organization for organization in organizations if organization.service_languages
        )
        scores = tuple(
            (person.weight, _best_service_access_score(person, service_organizations))
            for person in people
        )
        weighted_score = sum(weight * score for weight, score in scores)
        limited_access_weight = sum(
            weight for weight, score in scores if service_organizations and score < 50
        )
        interpreter_need_weight = sum(
            person.weight for person in people if person.language_profile.interpreter_needed
        )
        bridge_weight = sum(
            person.weight
            for person in people
            if sum(1 for skill in person.language_profile.skills if skill.can_bridge()) >= 2
        )
        return cls(
            total_people_weight=total_weight,
            organizations_with_service_languages=float(len(service_organizations)),
            average_service_access_score=weighted_score / population,
            limited_access_share=limited_access_weight / population,
            interpreter_need_share=interpreter_need_weight / population,
            multilingual_bridge_share=bridge_weight / population,
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "total_people_weight": self.total_people_weight,
            "organizations_with_service_languages": self.organizations_with_service_languages,
            "average_service_access_score": self.average_service_access_score,
            "limited_access_share": self.limited_access_share,
            "interpreter_need_share": self.interpreter_need_share,
            "multilingual_bridge_share": self.multilingual_bridge_share,
        }


def _best_service_access_score(
    person: PersonAgent,
    organizations: tuple[OrganizationAgent, ...],
) -> float:
    return max(
        (language_service_access_score(person, organization) for organization in organizations),
        default=50.0,
    )


@dataclass(frozen=True)
class InventoryStatusView(View):
    name: ClassVar[str] = "inventory_status"
    source_dependencies: ClassVar[tuple[str, ...]] = ("inventories",)

    inventory_records: float
    low_inventory_records: float
    stockout_risk: float
    reserve_gap_days: float
    cold_chain_exposure_records: float
    spoilage_risk: float

    @classmethod
    def derive(cls, state: CityState) -> InventoryStatusView:
        return cls.derive_from_inventories(state.inventories)

    @classmethod
    def derive_from_inventories(
        cls,
        inventories: tuple[InventoryState, ...],
    ) -> InventoryStatusView:
        low_inventory_records = sum(
            1.0 for inventory in inventories if inventory.reorder_gap_days > 0
        )
        cold_chain_exposure_records = sum(
            1.0
            for inventory in inventories
            if inventory.cold_chain_dependent and inventory.spoilage_risk > 0
        )
        return cls(
            inventory_records=float(len(inventories)),
            low_inventory_records=low_inventory_records,
            stockout_risk=sum(inventory.effective_stockout_risk for inventory in inventories),
            reserve_gap_days=sum(inventory.reserve_gap_days for inventory in inventories),
            cold_chain_exposure_records=cold_chain_exposure_records,
            spoilage_risk=sum(inventory.spoilage_risk for inventory in inventories),
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "inventory_records": self.inventory_records,
            "low_inventory_records": self.low_inventory_records,
            "stockout_risk": self.stockout_risk,
            "reserve_gap_days": self.reserve_gap_days,
            "cold_chain_exposure_records": self.cold_chain_exposure_records,
            "spoilage_risk": self.spoilage_risk,
        }


@dataclass(frozen=True)
class ParcelDevelopmentView(View):
    name: ClassVar[str] = "parcel_development"
    source_dependencies: ClassVar[tuple[str, ...]] = (
        "parcel_grid",
        "parcels",
        "households",
        "organizations",
    )

    parcel_count: float
    buildable_housing_capacity: float
    buildable_job_capacity: float
    underused_parcels: float
    redevelopment_candidate_parcels: float
    vacant_or_undeveloped_parcels: float
    utility_ready_parcels: float
    environmentally_constrained_parcels: float
    assessed_value: float
    average_customer_access_steps: float
    average_labor_access_steps: float

    @classmethod
    def derive(cls, state: CityState) -> ParcelDevelopmentView:
        parcels = tuple(state.parcels.values())
        household_parcel_ids = tuple(
            household.parcel_id for household in state.households if household.parcel_id
        )
        worker_parcel_ids = tuple(person.parcel_id for person in state.people if person.parcel_id)
        organization_parcel_ids = tuple(
            organization.parcel_id
            for organization in state.organizations
            if organization.parcel_id
        )
        return cls(
            parcel_count=float(len(parcels)),
            buildable_housing_capacity=sum(_buildable_housing_capacity(parcel) for parcel in parcels),
            buildable_job_capacity=sum(_buildable_job_capacity(parcel) for parcel in parcels),
            underused_parcels=sum(1.0 for parcel in parcels if parcel.underused),
            redevelopment_candidate_parcels=sum(
                1.0 for parcel in parcels if _is_redevelopment_candidate(parcel)
            ),
            vacant_or_undeveloped_parcels=sum(
                1.0 for parcel in parcels if _is_vacant_or_undeveloped(parcel)
            ),
            utility_ready_parcels=sum(1.0 for parcel in parcels if _is_utility_ready(parcel)),
            environmentally_constrained_parcels=sum(
                1.0 for parcel in parcels if _is_environmentally_constrained(parcel)
            ),
            assessed_value=sum(parcel.assessed_value for parcel in parcels),
            average_customer_access_steps=_average_nearest_distance(
                state,
                organization_parcel_ids,
                household_parcel_ids,
            ),
            average_labor_access_steps=_average_nearest_distance(
                state,
                organization_parcel_ids,
                worker_parcel_ids or household_parcel_ids,
            ),
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "parcel_count": self.parcel_count,
            "buildable_housing_capacity": self.buildable_housing_capacity,
            "buildable_job_capacity": self.buildable_job_capacity,
            "underused_parcels": self.underused_parcels,
            "redevelopment_candidate_parcels": self.redevelopment_candidate_parcels,
            "vacant_or_undeveloped_parcels": self.vacant_or_undeveloped_parcels,
            "utility_ready_parcels": self.utility_ready_parcels,
            "environmentally_constrained_parcels": self.environmentally_constrained_parcels,
            "assessed_value": self.assessed_value,
            "average_customer_access_steps": self.average_customer_access_steps,
            "average_labor_access_steps": self.average_labor_access_steps,
        }


def _buildable_housing_capacity(parcel: Parcel) -> float:
    if not _allows_any(parcel, ("residential", "mixed_use")):
        return 0.0
    if _is_environmentally_constrained(parcel):
        return 0.0
    return max(parcel.max_housing_units - parcel.housing_units, 0.0)


def _buildable_job_capacity(parcel: Parcel) -> float:
    if not _allows_any(parcel, ("commercial", "industrial", "mixed_use", "civic")):
        return 0.0
    if _is_environmentally_constrained(parcel):
        return 0.0
    return max(parcel.max_jobs - parcel.jobs, 0.0)


def _allows_any(parcel: Parcel, uses: tuple[str, ...]) -> bool:
    return any(use in parcel.zoning.allowed_uses for use in uses)


def _is_redevelopment_candidate(parcel: Parcel) -> bool:
    if _is_environmentally_constrained(parcel):
        return False
    has_capacity = (
        max(parcel.max_housing_units - parcel.housing_units, 0.0)
        + max(parcel.max_jobs - parcel.jobs, 0.0)
        > 0
    )
    return has_capacity and (
        parcel.underused
        or parcel.vacancy_rate >= 0.2
        or parcel.development_stage in {"vacant", "underused", "redeveloping"}
    )


def _is_vacant_or_undeveloped(parcel: Parcel) -> bool:
    return parcel.development_stage in {"pristine", "undeveloped", "vacant"}


def _is_utility_ready(parcel: Parcel) -> bool:
    return not any(
        constraint
        in {
            "utility_unready",
            "no_water_service",
            "no_sewer_service",
            "no_power_service",
            "road_access_gap",
        }
        for constraint in parcel.constraints
    )


def _is_environmentally_constrained(parcel: Parcel) -> bool:
    if parcel.natural_cover in {"lake", "ocean", "pond", "river", "wetland"}:
        return True
    return any(
        constraint
        in {
            "environmental_constraint",
            "floodplain",
            "habitat_preservation",
            "steep_slope",
            "wetland_buffer",
        }
        for constraint in parcel.constraints
    )


def _average_nearest_distance(
    state: CityState,
    origin_ids: tuple[str, ...],
    destination_ids: tuple[str, ...],
) -> float:
    if not origin_ids or not destination_ids:
        return 0.0
    distances = tuple(
        min(parcel_grid_distance(state, origin_id, destination_id) for destination_id in destination_ids)
        for origin_id in origin_ids
        if origin_id in state.parcels
    )
    if not distances:
        return 0.0
    return sum(distances) / len(distances)
