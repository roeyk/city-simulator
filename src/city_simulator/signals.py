from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from city_simulator.derived import _active_effect_amount, _density, _service_coverage
from city_simulator.state import CityPolicy, CityState, DelayedEffect, SignalLedger
from city_simulator.views import LanguageAccessView

DRIVER_BASELINE = "baseline_dynamics"
DRIVER_DELAYED_EFFECTS = "delayed_effects"
DRIVER_ENVIRONMENT = "environment_seasonality"
DRIVER_FEEDBACK = "feedback_loop"
DRIVER_INSTITUTIONAL = "institutional_behavior"
DRIVER_POLICY = "policy"
DRIVER_REGIONAL = "regional_spillover"
DRIVER_RESIDENT = "resident_household_behavior"
DRIVER_MARKET = "market_forces"
DRIVER_SUPPLY_CHAIN = "supply_chain"


@dataclass(frozen=True)
class SignalContext:
    state: CityState
    policy: CityPolicy
    infrastructure: float
    pollution: float


@dataclass(frozen=True)
class SignalConcept:
    name: str
    need: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    channels: tuple[str, ...]
    collect: Callable[[SignalContext, SignalLedger], None]


def signal_ledger_for_turn(context: SignalContext) -> SignalLedger:
    ledger = SignalLedger()
    for concept in SIGNAL_CONCEPTS:
        concept.collect(context, ledger)
    return ledger


def add_seasonal_signals(context: SignalContext, ledger: SignalLedger) -> None:
    _add_seasonal_signals(
        ledger=ledger,
        state=context.state,
        policy=context.policy,
        infrastructure=context.infrastructure,
        pollution=context.pollution,
    )


def add_language_access_signals(context: SignalContext, ledger: SignalLedger) -> None:
    state = context.state
    if not state.people or not any(
        organization.service_languages for organization in state.organizations
    ):
        return
    view = LanguageAccessView.derive(state)
    access_gap = max(50.0 - view.average_service_access_score, 0.0)
    if access_gap > 0:
        ledger.add(
            "language_service_access_gap",
            access_gap,
            "Language gaps reduce practical access to organizations with declared service languages.",
            driver_categories=(DRIVER_RESIDENT, DRIVER_INSTITUTIONAL),
        )
    if view.limited_access_share > 0:
        ledger.add(
            "language_limited_access",
            view.limited_access_share * 100,
            "Residents with low language overlap face practical service-access barriers.",
            driver_categories=(DRIVER_RESIDENT, DRIVER_INSTITUTIONAL),
        )
    if view.interpreter_need_share > 0:
        ledger.add(
            "interpreter_need",
            view.interpreter_need_share * 100,
            "Residents needing interpreters require language-access capacity from public and service organizations.",
            driver_categories=(DRIVER_RESIDENT, DRIVER_INSTITUTIONAL),
        )
    if view.multilingual_bridge_share > 0:
        ledger.add(
            "multilingual_bridge_capacity",
            view.multilingual_bridge_share * 100,
            "Multilingual residents can bridge households, services, employers, and community organizations.",
            driver_categories=(DRIVER_RESIDENT, DRIVER_INSTITUTIONAL),
        )


def add_sector_market_signals(context: SignalContext, ledger: SignalLedger) -> None:
    for balance in context.state.sector_market_balances:
        label = f"{balance.sector} {balance.good_or_service}".strip()
        local_gap = balance.local_supply_gap
        if local_gap > 0:
            ledger.add(
                "sector_local_supply_gap",
                local_gap,
                f"{label} demand exceeds local supply before imports or substitution.",
                driver_categories=(DRIVER_MARKET, DRIVER_SUPPLY_CHAIN),
            )
        if balance.imports > 0:
            ledger.add(
                "regional_import_dependency",
                balance.imports,
                f"{label} relies on imports from outside the city.",
                driver_categories=(DRIVER_REGIONAL, DRIVER_SUPPLY_CHAIN, DRIVER_MARKET),
            )
        unmet = balance.effective_unmet_demand
        if unmet > 0:
            ledger.add(
                "sector_unmet_demand",
                unmet,
                f"{label} demand remains unmet after local supply, imports, inventory, and substitution.",
                driver_categories=(DRIVER_MARKET, DRIVER_SUPPLY_CHAIN, DRIVER_REGIONAL),
            )
        if balance.price_pressure > 0:
            ledger.add(
                "sector_price_pressure",
                balance.price_pressure,
                f"{label} has price pressure from demand, supply, or logistics constraints.",
                driver_categories=(DRIVER_MARKET, DRIVER_SUPPLY_CHAIN),
            )
        if balance.wait_pressure > 0:
            ledger.add(
                "sector_wait_pressure",
                balance.wait_pressure,
                f"{label} has wait pressure from constrained service capacity.",
                driver_categories=(DRIVER_MARKET, DRIVER_INSTITUTIONAL),
            )
        if balance.utilization >= 0.95:
            ledger.add(
                "sector_capacity_strain",
                balance.utilization * 100,
                f"{label} is operating near or above practical capacity.",
                driver_categories=(DRIVER_MARKET, DRIVER_INSTITUTIONAL),
            )


SIGNAL_CONCEPTS: tuple[SignalConcept, ...] = (
    SignalConcept(
        name="seasonal_heat_cascade",
        need=(
            "Expose heat, cooling demand, grid, healthcare, and civic-trust signals "
            "before delayed effects or headline metrics consume them."
        ),
        inputs=(
            "state.population",
            "state.demographics",
            "state.physical_profile",
            "state.neighborhoods",
            "state.service_capacity",
            "state.pending_effects",
            "policy.environment_investment",
            "infrastructure",
            "pollution",
        ),
        outputs=("SignalLedger", "DelayedEffect candidates"),
        channels=(
            "summer_heat_exposure",
            "cooling_demand",
            "grid_shortfall",
            "healthcare_surge",
            "civic_trust_risk",
        ),
        collect=add_seasonal_signals,
    ),
    SignalConcept(
        name="language_service_access",
        need=(
            "Expose service-access gaps between resident language profiles and "
            "organization service-language capacity without directly changing headlines."
        ),
        inputs=("state.people.language_profile", "state.organizations.service_languages"),
        outputs=("SignalLedger",),
        channels=(
            "language_service_access_gap",
            "language_limited_access",
            "interpreter_need",
            "multilingual_bridge_capacity",
        ),
        collect=add_language_access_signals,
    ),
    SignalConcept(
        name="sector_market_balance",
        need=(
            "Expose sector demand, local supply, imports, exports, inventory or capacity "
            "drawdown, substitution, unmet demand, and price or wait pressure before "
            "business, service, or sentiment outcomes consume them."
        ),
        inputs=("state.sector_market_balances",),
        outputs=("SignalLedger",),
        channels=(
            "sector_local_supply_gap",
            "regional_import_dependency",
            "sector_unmet_demand",
            "sector_price_pressure",
            "sector_wait_pressure",
            "sector_capacity_strain",
        ),
        collect=add_sector_market_signals,
    ),
)

def _seasonal_signal_ledger(
    state: CityState,
    policy: CityPolicy,
    infrastructure: float,
    pollution: float,
) -> SignalLedger:
    ledger = SignalLedger()
    _add_seasonal_signals(
        ledger=ledger,
        state=state,
        policy=policy,
        infrastructure=infrastructure,
        pollution=pollution,
    )
    return ledger


def _add_seasonal_signals(
    ledger: SignalLedger,
    state: CityState,
    policy: CityPolicy,
    infrastructure: float,
    pollution: float,
) -> None:
    heat_exposure = _summer_heat_exposure(state, pollution)
    if heat_exposure <= 0:
        return

    seniors_share = state.demographics.seniors / max(state.population, 1.0)
    cooling_demand = heat_exposure * (1.0 + seniors_share * 1.8) * state.population / 100_000
    grid_resilience = _grid_resilience(state, infrastructure)
    grid_shortfall = max(cooling_demand - grid_resilience, 0.0)
    healthcare_surge = _healthcare_surge(
        state=state,
        heat_exposure=heat_exposure,
        grid_shortfall=grid_shortfall,
    )
    civic_trust_risk = grid_shortfall * 0.4 + healthcare_surge * 0.35
    mitigation = policy.environment_investment / 80_000_000

    ledger.add(
        "summer_heat_exposure",
        heat_exposure,
        "Summer heat exposure comes from climate profile, pollution, density, and active heat effects.",
        driver_categories=(DRIVER_ENVIRONMENT, DRIVER_BASELINE, DRIVER_DELAYED_EFFECTS),
    )
    ledger.add(
        "cooling_demand",
        cooling_demand,
        "Cooling demand increases with heat exposure, population, and senior vulnerability.",
        driver_categories=(DRIVER_ENVIRONMENT, DRIVER_RESIDENT),
    )
    ledger.add(
        "grid_shortfall",
        max(grid_shortfall - mitigation, 0.0),
        "Cooling demand exceeds grid resilience after policy mitigation.",
        driver_categories=(DRIVER_ENVIRONMENT, DRIVER_INSTITUTIONAL, DRIVER_POLICY),
    )
    ledger.add(
        "healthcare_surge",
        healthcare_surge,
        "Heat exposure and grid shortfall increase EMS and hospital load.",
        driver_categories=(DRIVER_ENVIRONMENT, DRIVER_INSTITUTIONAL),
    )
    ledger.add(
        "civic_trust_risk",
        max(civic_trust_risk - mitigation, 0.0),
        "Visible outages and health-system stress create civic trust risk.",
        driver_categories=(DRIVER_FEEDBACK, DRIVER_ENVIRONMENT, DRIVER_POLICY),
    )


def _summer_heat_exposure(state: CityState, pollution: float) -> float:
    climate_heat = _profile_value(state.physical_profile, ("seasonal_exposure", "summer_heat"))
    climate_heat += _profile_value(state.physical_profile, ("climate", "summer_heat"))
    neighborhood_heat = _neighborhood_exposure(state, "summer_heat")
    density_heat = max(_density(state.population, state) - 2_500, 0.0) / 900
    pollution_heat = max(pollution - 50.0, 0.0) * 0.22
    pending_heat = _active_effect_amount(state, "heat_exposure")
    return max(climate_heat + neighborhood_heat + density_heat + pollution_heat + pending_heat, 0.0)


def _profile_value(profile: dict[str, dict[str, float] | float], path: tuple[str, str]) -> float:
    section = profile.get(path[0])
    if isinstance(section, dict):
        value = section.get(path[1], 0.0)
        return float(value) if isinstance(value, int | float) else 0.0
    return 0.0


def _neighborhood_exposure(state: CityState, key: str) -> float:
    if not state.neighborhoods:
        return 0.0
    population_weighted = 0.0
    total_population = 0.0
    for neighborhood in state.neighborhoods.values():
        exposure = neighborhood.environmental_exposure.get(key, 0.0)
        if not isinstance(exposure, int | float):
            continue
        weight = max(neighborhood.population, 0.0)
        population_weighted += exposure * weight
        total_population += weight
    if total_population <= 0:
        exposures = [
            exposure
            for neighborhood in state.neighborhoods.values()
            if isinstance((exposure := neighborhood.environmental_exposure.get(key, 0.0)), int | float)
        ]
        return sum(exposures) / max(len(exposures), 1)
    return population_weighted / total_population


def _grid_resilience(state: CityState, infrastructure: float) -> float:
    grid_capacity = (
        state.service_capacity("electric_grid")
        + state.service_capacity("power")
        + state.service_capacity("utility_power")
    )
    capacity_bonus = grid_capacity / max(state.population / 10_000, 1.0) * 0.6
    repair_backlog = max(_active_effect_amount(state, "infrastructure_backlog"), 0.0)
    backlog_drag = repair_backlog / 5_000_000
    return max(infrastructure / 8 + capacity_bonus - backlog_drag, 0.0)


def _healthcare_surge(
    state: CityState,
    heat_exposure: float,
    grid_shortfall: float,
) -> float:
    healthcare_capacity = (
        state.service_capacity("healthcare")
        + state.service_capacity("emergency_care")
        + state.service_capacity("hospital")
        + state.service_capacity("clinic")
    )
    if healthcare_capacity <= 0:
        healthcare_capacity = state.population / 2_000 * _service_coverage(state) / 100
    capacity_buffer = healthcare_capacity / max(state.population / 10_000, 1.0) / 5
    delayed_surge = max(_active_effect_amount(state, "healthcare_surge"), 0.0)
    return max(heat_exposure * 0.35 + grid_shortfall * 0.65 + delayed_surge - capacity_buffer, 0.0)


def _delayed_effects_from_signals(ledger: SignalLedger) -> tuple[DelayedEffect, ...]:
    effects: list[DelayedEffect] = []
    grid_shortfall = ledger.get("grid_shortfall")
    healthcare_surge = ledger.get("healthcare_surge")
    civic_trust_risk = ledger.get("civic_trust_risk")
    if grid_shortfall >= 5.0:
        effects.append(
            DelayedEffect(
                source="seasonal_heat_cascade",
                target="infrastructure_backlog",
                amount=grid_shortfall * 750_000,
                duration_turns=3,
                decay_rate=0.35,
                tags=("heat", "grid", "repair_backlog"),
                explanation="Summer cooling demand created grid repair backlog.",
            )
        )
    if healthcare_surge >= 5.0:
        effects.append(
            DelayedEffect(
                source="seasonal_heat_cascade",
                target="healthcare_surge",
                amount=healthcare_surge,
                duration_turns=2,
                decay_rate=0.45,
                tags=("heat", "healthcare", "ems"),
                explanation="Heat exposure and outages created lingering healthcare load.",
            )
        )
    if civic_trust_risk >= 4.0:
        effects.append(
            DelayedEffect(
                source="seasonal_heat_cascade",
                target="civic_trust",
                amount=-civic_trust_risk,
                delay_turns=1,
                duration_turns=3,
                decay_rate=0.4,
                tags=("heat", "grid", "public_trust"),
                explanation="Outages and visible heat-health strain damaged confidence in city response.",
            )
        )
    return tuple(effects)
