from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, TypeVar

from city_simulator.state import CityState

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
