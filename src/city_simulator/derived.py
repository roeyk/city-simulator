from __future__ import annotations

from city_simulator.state import CityState, DelayedEffect


def active_delayed_effects(state: CityState, target: str | None = None) -> tuple[DelayedEffect, ...]:
    effects = tuple(effect for effect in state.pending_effects if effect.is_active)
    if target is None:
        return effects
    return tuple(effect for effect in effects if effect.target == target)


def _active_effect_amount(state: CityState, target: str) -> float:
    return sum(effect.amount for effect in active_delayed_effects(state, target))


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


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)
