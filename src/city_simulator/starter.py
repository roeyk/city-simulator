from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, replace
from pathlib import Path

from city_simulator.model import CityState, Demographics
from city_simulator.starter_profiles import (
    DEFAULT_ADULT_FAMILY_STATS,
    DEFAULT_AGE_MIX,
    DEFAULT_CIVIC_ASSETS,
    DEFAULT_DEVELOPMENT_MIX,
    DEFAULT_EDUCATION_MIX,
    DEFAULT_GRADUATION_MIX,
    DEFAULT_INCOME_MIX,
    DEFAULT_LITERACY_MIX,
    DEFAULT_NATIONALITY_MIX,
    DEFAULT_ORIENTATION_MIX,
    DEFAULT_RACE_MIX,
    DEFAULT_RELIGION_MIX,
    DEFAULT_RELIGIOSITY_MIX,
    DEFAULT_SEX_MIX,
    DEFAULT_TERRAIN_MIX,
    DEFAULT_WORKFORCE_MIX,
    STARTER_PRESETS,
)
from city_simulator.storage import city_path, ensure_data_dirs


def starter_city(name: str = "balanced", population: float | None = None) -> CityState:
    if name not in STARTER_PRESETS:
        choices = ", ".join(sorted(STARTER_PRESETS))
        raise ValueError(f"unknown city preset {name!r}; choose one of: {choices}")
    state = STARTER_PRESETS[name]
    if population is None:
        return state
    return _scale_population(state, population)


def write_starter_city(
    path: str | Path,
    name: str = "balanced",
    population: float | None = None,
) -> CityState:
    state = starter_city(name, population)
    ensure_data_dirs()
    destination = city_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
    return state


def prompt_for_starter_city(
    input_func: Callable[[str], str] | None = None,
    output_func: Callable[[str], None] = print,
) -> CityState:
    if input_func is None:
        input_func = input
    output_func("Create a new city. Press Enter to accept defaults.")
    population = _prompt_float(input_func, "Population", 100_000)
    age_mix = _prompt_percent_mix(input_func, "age groups", DEFAULT_AGE_MIX)
    race_mix = _prompt_percent_mix(input_func, "races", DEFAULT_RACE_MIX)
    sex_mix = _prompt_percent_mix(input_func, "sexes", DEFAULT_SEX_MIX)
    orientation_mix = _prompt_percent_mix(input_func, "sexual orientation", DEFAULT_ORIENTATION_MIX)
    nationality_mix = _prompt_percent_mix(input_func, "nationalities", DEFAULT_NATIONALITY_MIX)
    religion_mix = _prompt_percent_mix(input_func, "religions", DEFAULT_RELIGION_MIX)
    religiosity_mix = _prompt_nested_percent_mix(
        input_func,
        "religiosity by religion",
        religion_mix,
        DEFAULT_RELIGIOSITY_MIX,
    )
    education_mix = _prompt_percent_mix(input_func, "education levels", DEFAULT_EDUCATION_MIX)
    literacy_age_mix = _prompt_nested_percent_mix(
        input_func,
        "literacy by age group",
        age_mix,
        DEFAULT_LITERACY_MIX,
    )
    graduation_age_mix = _prompt_nested_percent_mix(
        input_func,
        "school graduation by age group",
        age_mix,
        DEFAULT_GRADUATION_MIX,
    )
    income_mix = _prompt_percent_mix(input_func, "income levels", DEFAULT_INCOME_MIX)
    age_income_mix = _prompt_age_income_mix(input_func, age_mix, income_mix)
    workforce_mix = _prompt_percent_mix(input_func, "workforce categories", DEFAULT_WORKFORCE_MIX)
    adult_family = _prompt_metric_set(
        input_func,
        "adult family stats, as % of adults 18+",
        DEFAULT_ADULT_FAMILY_STATS,
    )
    area_square_miles = _prompt_float(input_func, "Physical size in square miles", 55)
    terrain_mix = _prompt_percent_mix(input_func, "terrain/coverage mix", DEFAULT_TERRAIN_MIX)
    development_mix = _prompt_percent_mix(input_func, "development mix", DEFAULT_DEVELOPMENT_MIX)
    civic_assets = _prompt_metric_set(input_func, "civic assets and districts", DEFAULT_CIVIC_ASSETS)
    return custom_city_from_percentages(
        population=population,
        age_mix=age_mix,
        race_mix=race_mix,
        sex_mix=sex_mix,
        orientation_mix=orientation_mix,
        nationality_mix=nationality_mix,
        religion_mix=religion_mix,
        religiosity_mix=religiosity_mix,
        education_mix=education_mix,
        literacy_age_mix=literacy_age_mix,
        graduation_age_mix=graduation_age_mix,
        income_mix=income_mix,
        age_income_mix=age_income_mix,
        workforce_mix=workforce_mix,
        adult_family=adult_family,
        area_square_miles=area_square_miles,
        terrain_mix=terrain_mix,
        development_mix=development_mix,
        civic_assets=civic_assets,
    )


def custom_city_from_percentages(
    population: float,
    age_mix: dict[str, float],
    race_mix: dict[str, float],
    sex_mix: dict[str, float],
    nationality_mix: dict[str, float],
    education_mix: dict[str, float],
    income_mix: dict[str, float],
    adult_family: dict[str, float],
    orientation_mix: dict[str, float] | None = None,
    religion_mix: dict[str, float] | None = None,
    religiosity_mix: dict[str, dict[str, float]] | None = None,
    literacy_age_mix: dict[str, dict[str, float]] | None = None,
    graduation_age_mix: dict[str, dict[str, float]] | None = None,
    age_income_mix: dict[str, dict[str, float]] | None = None,
    workforce_mix: dict[str, float] | None = None,
    area_square_miles: float = 55.0,
    terrain_mix: dict[str, float] | None = None,
    development_mix: dict[str, float] | None = None,
    civic_assets: dict[str, float] | None = None,
) -> CityState:
    if population <= 0:
        raise ValueError("population must be positive")
    if area_square_miles <= 0:
        raise ValueError("area_square_miles must be positive")
    terrain = terrain_mix or DEFAULT_TERRAIN_MIX
    development = development_mix or DEFAULT_DEVELOPMENT_MIX
    assets = civic_assets or DEFAULT_CIVIC_ASSETS
    orientation = orientation_mix or DEFAULT_ORIENTATION_MIX
    religion = religion_mix or DEFAULT_RELIGION_MIX
    religiosity = religiosity_mix or _default_nested_mix(religion, DEFAULT_RELIGIOSITY_MIX)
    literacy_age = literacy_age_mix or _default_nested_mix(age_mix, DEFAULT_LITERACY_MIX)
    graduation_age = graduation_age_mix or _default_nested_mix(age_mix, DEFAULT_GRADUATION_MIX)
    _validate_percent_mix(age_mix, "age groups")
    _validate_percent_mix(race_mix, "races")
    _validate_percent_mix(sex_mix, "sexes")
    _validate_percent_mix(orientation, "sexual orientation")
    _validate_percent_mix(nationality_mix, "nationalities")
    _validate_percent_mix(religion, "religions")
    _validate_nested_percent_mix(religiosity, religion, "religiosity by religion")
    _validate_percent_mix(education_mix, "education levels")
    _validate_nested_percent_mix(literacy_age, age_mix, "literacy by age group")
    _validate_nested_percent_mix(graduation_age, age_mix, "school graduation by age group")
    _validate_percent_mix(income_mix, "income levels")
    age_income = age_income_mix or _default_age_income_mix(age_mix, income_mix)
    workforce = workforce_mix or DEFAULT_WORKFORCE_MIX
    _validate_age_income_mix(age_income, age_mix)
    _validate_percent_mix(workforce, "workforce categories")
    _validate_metric_set(adult_family, "adult family stats")
    _validate_percent_mix(terrain, "terrain/coverage mix")
    _validate_percent_mix(development, "development mix")
    _validate_metric_set(assets, "civic assets")

    adults = population * (100.0 - age_mix["under_18"]) / 100.0
    profile = {
        "age_percent": age_mix,
        "age_count": _counts(population, age_mix),
        "race_percent": race_mix,
        "race_count": _counts(population, race_mix),
        "sex_percent": sex_mix,
        "sex_count": _counts(population, sex_mix),
        "orientation_percent": orientation,
        "orientation_count": _counts(population, orientation),
        "nationality_percent": nationality_mix,
        "nationality_count": _counts(population, nationality_mix),
        "religion_percent": religion,
        "religion_count": _counts(population, religion),
        "religiosity_percent": religiosity,
        "religiosity_count": _nested_counts(population, religion, religiosity),
        "education_percent": education_mix,
        "education_count": _counts(adults, education_mix),
        "literacy_age_percent": literacy_age,
        "literacy_age_count": _nested_counts(population, age_mix, literacy_age),
        "graduation_age_percent": graduation_age,
        "graduation_age_count": _nested_counts(population, age_mix, graduation_age),
        "income_percent": income_mix,
        "income_count": _counts(population, income_mix),
        "age_income_percent": age_income,
        "age_income_count": _age_income_counts(population, age_mix, age_income),
        "workforce_percent": workforce,
        "workforce_count": _counts(population * (100.0 - age_mix["under_18"]) / 100.0, workforce),
        "adult_family_percent": adult_family,
        "adult_family_count": _counts(adults, adult_family),
    }
    cohort_profiles = {
        "age": {
            "income_percent": age_income,
            "income_count": _age_income_counts(population, age_mix, age_income),
            "literacy_percent": literacy_age,
            "literacy_count": _nested_counts(population, age_mix, literacy_age),
            "graduation_percent": graduation_age,
            "graduation_count": _nested_counts(population, age_mix, graduation_age),
        },
        "religion": {
            "religiosity_percent": religiosity,
            "religiosity_count": _nested_counts(population, religion, religiosity),
        },
        "workforce": {
            "category_percent": workforce,
            "category_count": _counts(adults, workforce),
        },
    }
    physical_profile = {
        "area_square_miles": area_square_miles,
        "population_density_per_square_mile": population / area_square_miles,
        "terrain_percent": terrain,
        "terrain_square_miles": _counts(area_square_miles, terrain),
        "development_percent": development,
        "development_square_miles": _counts(area_square_miles, development),
    }
    demographics = Demographics(
        children=profile["age_count"]["under_18"],
        working_age=profile["age_count"]["age_18_34"] + profile["age_count"]["age_35_64"],
        seniors=profile["age_count"]["age_65_plus"],
        low_income=profile["income_count"]["low"],
        middle_income=profile["income_count"]["middle"],
        high_income=profile["income_count"]["high"],
    )
    return replace(
        CityState(),
        population=population,
        demographics=demographics,
        population_profile=profile,
        cohort_profiles=cohort_profiles,
        physical_profile=physical_profile,
        civic_assets=assets,
        housing_units=population / 2.35,
        jobs=demographics.working_age * 0.94,
        budget=population * 1_250,
    )


def _scale_population(state: CityState, population: float) -> CityState:
    if population <= 0:
        raise ValueError("population must be positive")
    factor = population / state.population
    return replace(
        state,
        population=population,
        demographics=Demographics(
            children=state.demographics.children * factor,
            working_age=state.demographics.working_age * factor,
            seniors=state.demographics.seniors * factor,
            low_income=state.demographics.low_income * factor,
            middle_income=state.demographics.middle_income * factor,
            high_income=state.demographics.high_income * factor,
        ),
        housing_units=state.housing_units * factor,
        jobs=state.jobs * factor,
        budget=state.budget * factor,
    )


def _prompt_float(input_func: Callable[[str], str], label: str, default: float) -> float:
    raw = input_func(f"{label} [{default:,.0f}]: ").strip()
    if not raw:
        return default
    value = float(raw.replace(",", ""))
    if value <= 0:
        raise ValueError(f"{label.lower()} must be positive")
    return value


def _prompt_percent_mix(
    input_func: Callable[[str], str],
    label: str,
    defaults: dict[str, float],
) -> dict[str, float]:
    values: dict[str, float | None] = {}
    displayed_defaults: dict[str, float] = {}
    print(f"{label} percentages:")
    items = list(defaults.items())
    for index, (key, _default) in enumerate(items):
        assigned_for_prompt = _assigned_prompt_total(values, displayed_defaults)
        default = _estimated_auto_share(items, values, displayed_defaults, index)
        displayed_defaults[key] = default
        raw = input_func(
            f"  {key} [{default:g}; remaining {100.0 - assigned_for_prompt:g}]: "
        ).strip()
        values[key] = None if not raw else float(raw)
    resolved = _resolve_auto_percentages(values, defaults, label)
    _validate_percent_mix(resolved, label)
    return resolved


def _prompt_age_income_mix(
    input_func: Callable[[str], str],
    age_mix: dict[str, float],
    income_mix: dict[str, float],
) -> dict[str, dict[str, float]]:
    print("age-by-income percentages within each age group:")
    return {
        age_group: _prompt_percent_mix(input_func, f"  {age_group} income levels", income_mix)
        for age_group in age_mix
    }


def _prompt_nested_percent_mix(
    input_func: Callable[[str], str],
    label: str,
    parent_mix: dict[str, float],
    child_defaults: dict[str, float],
) -> dict[str, dict[str, float]]:
    print(f"{label}:")
    return {
        parent: _prompt_percent_mix(input_func, f"  {parent}", child_defaults)
        for parent in parent_mix
    }


def _prompt_metric_set(
    input_func: Callable[[str], str],
    label: str,
    defaults: dict[str, float],
) -> dict[str, float]:
    default_text = _format_mix(defaults)
    raw = input_func(f"{label} [{default_text}]: ").strip()
    values = defaults if not raw else _parse_key_values(raw)
    _validate_metric_set(values, label)
    return values


def _parse_key_values(raw: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for part in raw.split(","):
        if "=" not in part:
            raise ValueError("entries must use key=value format")
        key, value = part.split("=", 1)
        values[key.strip()] = float(value.strip())
    return values


def _validate_percent_mix(values: dict[str, float], label: str) -> None:
    _validate_metric_set(values, label)
    total = sum(values.values())
    if abs(total - 100.0) > 0.5:
        raise ValueError(f"{label} percentages must total 100, got {total:.1f}")


def _validate_metric_set(values: dict[str, float], label: str) -> None:
    if not values:
        raise ValueError(f"{label} cannot be empty")
    for key, value in values.items():
        if not key:
            raise ValueError(f"{label} contains an empty key")
        if not 0.0 <= value <= 100.0:
            raise ValueError(f"{label} value for {key} must be between 0 and 100")


def _counts(total: float, percentages: dict[str, float]) -> dict[str, float]:
    return {key: total * value / 100.0 for key, value in percentages.items()}


def _format_mix(values: dict[str, float]) -> str:
    return ", ".join(f"{key}={value:g}" for key, value in values.items())


def _default_age_income_mix(
    age_mix: dict[str, float],
    income_mix: dict[str, float],
) -> dict[str, dict[str, float]]:
    return {age_group: dict(income_mix) for age_group in age_mix}


def _default_nested_mix(
    parent_mix: dict[str, float],
    child_mix: dict[str, float],
) -> dict[str, dict[str, float]]:
    return {parent: dict(child_mix) for parent in parent_mix}


def _validate_age_income_mix(
    age_income_mix: dict[str, dict[str, float]],
    age_mix: dict[str, float],
) -> None:
    missing = sorted(set(age_mix) - set(age_income_mix))
    extra = sorted(set(age_income_mix) - set(age_mix))
    if missing or extra:
        raise ValueError(
            "age-by-income groups must match age groups"
            f"; missing={missing or 'none'}, extra={extra or 'none'}"
        )
    for age_group, income_split in age_income_mix.items():
        _validate_percent_mix(income_split, f"{age_group} income levels")


def _validate_nested_percent_mix(
    nested_mix: dict[str, dict[str, float]],
    parent_mix: dict[str, float],
    label: str,
) -> None:
    missing = sorted(set(parent_mix) - set(nested_mix))
    extra = sorted(set(nested_mix) - set(parent_mix))
    if missing or extra:
        raise ValueError(
            f"{label} groups must match parent groups"
            f"; missing={missing or 'none'}, extra={extra or 'none'}"
        )
    for parent, child_mix in nested_mix.items():
        _validate_percent_mix(child_mix, f"{label} for {parent}")


def _age_income_counts(
    population: float,
    age_mix: dict[str, float],
    age_income_mix: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    return {
        age_group: _counts(population * age_percent / 100.0, age_income_mix[age_group])
        for age_group, age_percent in age_mix.items()
    }


def _nested_counts(
    total: float,
    parent_mix: dict[str, float],
    nested_mix: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    return {
        parent: _counts(total * parent_percent / 100.0, nested_mix[parent])
        for parent, parent_percent in parent_mix.items()
    }


def _resolve_auto_percentages(
    values: dict[str, float | None],
    defaults: dict[str, float],
    label: str,
) -> dict[str, float]:
    explicit_total = sum(value for value in values.values() if value is not None)
    if explicit_total > 100.5:
        raise ValueError(f"{label} percentages exceed 100, got {explicit_total:.1f}")
    auto_keys = [key for key, value in values.items() if value is None]
    if not auto_keys:
        return {key: float(value) for key, value in values.items() if value is not None}

    remainder = max(0.0, 100.0 - explicit_total)
    default_total = sum(defaults[key] for key in auto_keys)
    if default_total <= 0:
        auto_share = remainder / len(auto_keys)
        return {key: auto_share if value is None else value for key, value in values.items()}
    return {
        key: remainder * defaults[key] / default_total if value is None else value
        for key, value in values.items()
    }


def _estimated_auto_share(
    items: list[tuple[str, float]],
    values: dict[str, float | None],
    displayed_defaults: dict[str, float],
    index: int,
) -> float:
    assigned = _assigned_prompt_total(values, displayed_defaults)
    remaining = max(0.0, 100.0 - assigned)
    remaining_items = items[index:]
    remaining_default_total = sum(default for _key, default in remaining_items)
    if len(remaining_items) == 1:
        return remaining
    if remaining_default_total <= 0:
        return remaining / len(remaining_items)
    return remaining * remaining_items[0][1] / remaining_default_total


def _assigned_prompt_total(
    values: dict[str, float | None],
    displayed_defaults: dict[str, float],
) -> float:
    total = 0.0
    for key, value in values.items():
        total += displayed_defaults[key] if value is None else value
    return total
