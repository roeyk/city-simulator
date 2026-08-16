from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Agent:
    agent_id: str
    weight: float = field(default=1.0, kw_only=True)


@dataclass(frozen=True)
class PersonAgent(Agent):
    household_id: str
    age: int
    income_band: str
    employment_status: str = "not_in_labor_force"
    health_status: str = "typical"
    neighborhood: str | None = None

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


@dataclass(frozen=True)
class OrganizationAgent(Agent):
    organization_type: str
    sector: str = "unspecified"
    neighborhood: str | None = None
    staff: float = 0.0
    operating_budget: float = 0.0
