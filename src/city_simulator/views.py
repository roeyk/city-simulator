from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, TypeVar

from city_simulator.agents import OrganizationAgent, PersonAgent, ServiceLanguage
from city_simulator.state import CityState, InventoryState

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
