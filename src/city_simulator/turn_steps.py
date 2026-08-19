from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from city_simulator.state import (
    CityPolicy,
    CityState,
    Demographics,
    ExternalControls,
    Issue,
    ModelParameters,
    SignalLedger,
)


@dataclass
class AnnualTurnContext:
    state: CityState
    policy: CityPolicy
    external: ExternalControls
    parameters: ModelParameters
    previous_issues: list[Issue] = field(default_factory=list)
    revenue: float | None = None
    expenses: float | None = None
    budget: float | None = None
    housing_units: float | None = None
    jobs_delta: float | None = None
    jobs: float | None = None
    infrastructure: float | None = None
    pollution: float | None = None
    housing_gap: float | None = None
    signal_ledger: SignalLedger | None = None
    work_pressure: float | None = None
    satisfaction: float | None = None
    population_delta: float | None = None
    population: float | None = None
    demographics: Demographics | None = None
    growth_rate: float | None = None
    labor_market: dict[str, float] | None = None
    crime: float | None = None
    sentiment_signals: dict[str, float] | None = None
    public_sentiment: float | None = None
    next_state: CityState | None = None
    active_issues: list[Issue] = field(default_factory=list)


@dataclass(frozen=True)
class TurnStep:
    name: str
    run: Callable[[AnnualTurnContext], None]
    requires: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()


def run_turn_steps(context: AnnualTurnContext, steps: tuple[TurnStep, ...]) -> AnnualTurnContext:
    for step in steps:
        step.run(context)
    return context
