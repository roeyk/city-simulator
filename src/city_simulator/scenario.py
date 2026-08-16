from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from city_simulator.model import (
    CityMetrics,
    CityPolicy,
    CitySensitivity,
    CityState,
    DelayedEffect,
    Demographics,
    EmbeddedService,
    ExternalControls,
    FinancialInstitutionProfile,
    HousingAssistance,
    HousingStock,
    Neighborhood,
    OperatingSchedule,
    PlaceAsset,
)
from city_simulator.storage import city_path, scenario_path


class ScenarioError(ValueError):
    """Raised when a city or scenario file cannot be loaded."""


def load_city(path: str | Path) -> CityState:
    data = _load_json_object(city_path(path))
    return city_from_mapping(data)


def save_city(path: str | Path, state: CityState) -> Path:
    resolved_path = city_path(path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")
    return resolved_path


def load_scenario(path: str | Path) -> tuple[str, CityPolicy, ExternalControls, int | None]:
    resolved_path = scenario_path(path)
    data = _load_json_object(resolved_path)
    name = str(data.get("name") or resolved_path.stem)
    years = data.get("years")
    if years is not None and (not isinstance(years, int) or years < 0):
        raise ScenarioError("scenario years must be a non-negative integer")
    policy_data = data.get("policy", data)
    if not isinstance(policy_data, dict):
        raise ScenarioError("scenario policy must be an object")
    external_data = _external_controls_data(data)
    return name, policy_from_mapping(policy_data), external_from_mapping(external_data), years


def city_from_mapping(data: dict[str, Any]) -> CityState:
    demographics_data = data.get("demographics", {})
    if not isinstance(demographics_data, dict):
        raise ScenarioError("city demographics must be an object")
    metrics_data = data.get("metrics", {})
    if not isinstance(metrics_data, dict):
        raise ScenarioError("city metrics must be an object")
    sensitivity_data = data.get("sensitivity", {})
    if not isinstance(sensitivity_data, dict):
        raise ScenarioError("city sensitivity must be an object")
    housing_stock_data = data.get("housing_stock", {})
    if not isinstance(housing_stock_data, dict):
        raise ScenarioError("city housing_stock must be an object")
    housing_assistance_data = data.get("housing_assistance", {})
    if not isinstance(housing_assistance_data, dict):
        raise ScenarioError("city housing_assistance must be an object")
    neighborhoods_data = data.get("neighborhoods", {})
    if not isinstance(neighborhoods_data, dict):
        raise ScenarioError("city neighborhoods must be an object")
    place_assets_data = data.get("place_assets", ())
    if not isinstance(place_assets_data, list | tuple):
        raise ScenarioError("city place_assets must be an array")
    pending_effects_data = data.get("pending_effects", ())
    if not isinstance(pending_effects_data, list | tuple):
        raise ScenarioError("city pending_effects must be an array")

    demographics = _dataclass_from_mapping(
        Demographics,
        demographics_data,
        "demographics",
    )
    metrics = _dataclass_from_mapping(
        CityMetrics,
        metrics_data,
        "metrics",
    )
    sensitivity = _dataclass_from_mapping(
        CitySensitivity,
        sensitivity_data,
        "sensitivity",
    )
    housing_stock = _dataclass_from_mapping(
        HousingStock,
        housing_stock_data,
        "housing_stock",
    )
    housing_assistance = _dataclass_from_mapping(
        HousingAssistance,
        housing_assistance_data,
        "housing_assistance",
    )
    neighborhoods = _neighborhoods_from_mapping(neighborhoods_data)
    place_assets = _place_assets_from_sequence(place_assets_data, "city place_assets")
    state_data = {
        key: value
        for key, value in data.items()
        if key
        not in {
            "demographics",
            "metrics",
            "sensitivity",
            "housing_stock",
            "housing_assistance",
            "neighborhoods",
            "place_assets",
            "pending_effects",
        }
    }
    return _dataclass_from_mapping(
        CityState,
        state_data
        | {
            "demographics": demographics,
            "metrics": metrics,
            "sensitivity": sensitivity,
            "housing_stock": housing_stock,
            "housing_assistance": housing_assistance,
            "neighborhoods": neighborhoods,
            "place_assets": place_assets,
            "pending_effects": _delayed_effects_from_sequence(
                pending_effects_data,
                "city pending_effects",
            ),
        },
        "city",
    )


def policy_from_mapping(data: dict[str, Any]) -> CityPolicy:
    return _dataclass_from_mapping(CityPolicy, data, "policy")


def external_from_mapping(data: dict[str, Any]) -> ExternalControls:
    return _dataclass_from_mapping(ExternalControls, data, "external controls")


def _neighborhoods_from_mapping(data: dict[str, Any]) -> dict[str, Neighborhood]:
    neighborhoods: dict[str, Neighborhood] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            raise ScenarioError(f"neighborhood {key} must be an object")
        housing_stock_data = value.get("housing_stock", {})
        if not isinstance(housing_stock_data, dict):
            raise ScenarioError(f"neighborhood {key} housing_stock must be an object")
        housing_assistance_data = value.get("housing_assistance", {})
        if not isinstance(housing_assistance_data, dict):
            raise ScenarioError(f"neighborhood {key} housing_assistance must be an object")
        place_assets_data = value.get("place_assets", ())
        if not isinstance(place_assets_data, list | tuple):
            raise ScenarioError(f"neighborhood {key} place_assets must be an array")
        neighborhood_data = {
            field_key: field_value
            for field_key, field_value in value.items()
            if field_key not in {"housing_stock", "housing_assistance", "place_assets"}
        }
        if "name" not in neighborhood_data:
            neighborhood_data["name"] = key
        if "adjacent_neighborhoods" in neighborhood_data:
            neighborhood_data["adjacent_neighborhoods"] = tuple(
                neighborhood_data["adjacent_neighborhoods"]
            )
        if "adjacent_sectors" in neighborhood_data:
            neighborhood_data["adjacent_sectors"] = tuple(neighborhood_data["adjacent_sectors"])
        neighborhoods[key] = _dataclass_from_mapping(
            Neighborhood,
            neighborhood_data
            | {
                "housing_stock": _dataclass_from_mapping(
                    HousingStock,
                    housing_stock_data,
                    f"neighborhood {key} housing_stock",
                ),
                "housing_assistance": _dataclass_from_mapping(
                    HousingAssistance,
                    housing_assistance_data,
                    f"neighborhood {key} housing_assistance",
                ),
                "place_assets": _place_assets_from_sequence(
                    place_assets_data,
                    f"neighborhood {key} place_assets",
                    default_neighborhood=key,
                ),
            },
            f"neighborhood {key}",
        )
    return neighborhoods


def _place_assets_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
    default_neighborhood: str | None = None,
) -> tuple[PlaceAsset, ...]:
    place_assets: list[PlaceAsset] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        services_data = value.get("services", ())
        if not isinstance(services_data, list | tuple):
            raise ScenarioError(f"{item_label} services must be an array")
        schedule_data = value.get("schedule", {})
        if not isinstance(schedule_data, dict):
            raise ScenarioError(f"{item_label} schedule must be an object")
        financial_profile_data = value.get("financial_profile")
        if financial_profile_data is not None and not isinstance(financial_profile_data, dict):
            raise ScenarioError(f"{item_label} financial_profile must be an object")
        place_asset_data = {
            field_key: field_value
            for field_key, field_value in value.items()
            if field_key not in {"services", "schedule", "financial_profile"}
        }
        if default_neighborhood is not None and "neighborhood" not in place_asset_data:
            place_asset_data["neighborhood"] = default_neighborhood
        _tupleize(place_asset_data, ("service_area", "tags"))
        place_assets.append(
            _dataclass_from_mapping(
                PlaceAsset,
                place_asset_data
                | {
                    "schedule": _operating_schedule_from_mapping(
                        schedule_data,
                        f"{item_label} schedule",
                    ),
                    "services": _embedded_services_from_sequence(
                        services_data,
                        f"{item_label} services",
                    ),
                    "financial_profile": _financial_profile_from_mapping(
                        financial_profile_data,
                        f"{item_label} financial_profile",
                    ),
                },
                item_label,
            )
        )
    return tuple(place_assets)


def _embedded_services_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[EmbeddedService, ...]:
    services: list[EmbeddedService] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        service_data = dict(value)
        schedule_data = service_data.pop("schedule", {})
        if not isinstance(schedule_data, dict):
            raise ScenarioError(f"{item_label} schedule must be an object")
        _tupleize(service_data, ("target_groups", "tags"))
        services.append(
            _dataclass_from_mapping(
                EmbeddedService,
                service_data
                | {
                    "schedule": _operating_schedule_from_mapping(
                        schedule_data,
                        f"{item_label} schedule",
                    )
                },
                item_label,
            )
        )
    return tuple(services)


def _operating_schedule_from_mapping(data: dict[str, Any], label: str) -> OperatingSchedule:
    schedule_data = dict(data)
    _tupleize(schedule_data, ("days", "seasons", "peak_periods"))
    return _dataclass_from_mapping(OperatingSchedule, schedule_data, label)


def _financial_profile_from_mapping(
    data: dict[str, Any] | None,
    label: str,
) -> FinancialInstitutionProfile | None:
    if data is None:
        return None
    profile_data = dict(data)
    _tupleize(profile_data, ("market_roles", "participant_roles", "asset_classes"))
    return _dataclass_from_mapping(FinancialInstitutionProfile, profile_data, label)


def _delayed_effects_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[DelayedEffect, ...]:
    effects: list[DelayedEffect] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        effect_data = dict(value)
        _tupleize(effect_data, ("tags",))
        effects.append(_dataclass_from_mapping(DelayedEffect, effect_data, item_label))
    return tuple(effects)


def _tupleize(data: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        if key in data:
            value = data[key]
            if not isinstance(value, list | tuple):
                raise ScenarioError(f"{key} must be an array")
            data[key] = tuple(value)


def _external_controls_data(data: dict[str, Any]) -> dict[str, Any]:
    external: dict[str, Any] = {}
    for level in ("county", "state", "country", "federal"):
        controls = data.get(level, {})
        if not isinstance(controls, dict):
            raise ScenarioError(f"scenario {level} controls must be an object")
        for key, value in controls.items():
            external[_external_key(level, key)] = value

    explicit_external = data.get("external", {})
    if not isinstance(explicit_external, dict):
        raise ScenarioError("scenario external controls must be an object")
    return external | explicit_external


def _external_key(level: str, key: str) -> str:
    if level == "country":
        if key in {"funding", "growth_pressure"}:
            return f"federal_{key}"
        return f"national_{key}"
    return f"{level}_{key}"


def _dataclass_from_mapping(model_type: type[Any], data: dict[str, Any], label: str) -> Any:
    field_names = {field.name for field in fields(model_type)}
    unknown = sorted(set(data) - field_names)
    if unknown:
        raise ScenarioError(f"unknown {label} fields: {', '.join(unknown)}")
    return model_type(**data)


def _load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise ScenarioError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ScenarioError(f"{path} must contain a JSON object")
    return data
