from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from city_simulator.model import (
    AdoptionIdentity,
    CityMetrics,
    CityPolicy,
    CityRevenueSources,
    CitySensitivity,
    CityState,
    CulturalAffiliation,
    CulturalIdentity,
    DelayedEffect,
    Demographics,
    EducationCompletion,
    EducationHistory,
    EmbeddedService,
    EmploymentRecord,
    ExternalControls,
    FinancialInstitutionProfile,
    HouseholdAgent,
    HousingAssistance,
    HousingStock,
    InventoryState,
    LanguageProfile,
    LanguageSkill,
    Neighborhood,
    OperatingSchedule,
    OrganizationAgent,
    PersonAgent,
    PlaceAsset,
    SectorMarketBalance,
    ServiceLanguage,
    ZoningEnvelope,
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
    revenue_sources_data = data.get("revenue_sources", {})
    if not isinstance(revenue_sources_data, dict):
        raise ScenarioError("city revenue_sources must be an object")
    neighborhoods_data = data.get("neighborhoods", {})
    if not isinstance(neighborhoods_data, dict):
        raise ScenarioError("city neighborhoods must be an object")
    place_assets_data = data.get("place_assets", ())
    if not isinstance(place_assets_data, list | tuple):
        raise ScenarioError("city place_assets must be an array")
    people_data = data.get("people", ())
    if not isinstance(people_data, list | tuple):
        raise ScenarioError("city people must be an array")
    households_data = data.get("households", ())
    if not isinstance(households_data, list | tuple):
        raise ScenarioError("city households must be an array")
    organizations_data = data.get("organizations", ())
    if not isinstance(organizations_data, list | tuple):
        raise ScenarioError("city organizations must be an array")
    sector_market_balances_data = data.get("sector_market_balances", ())
    if not isinstance(sector_market_balances_data, list | tuple):
        raise ScenarioError("city sector_market_balances must be an array")
    inventories_data = data.get("inventories", ())
    if not isinstance(inventories_data, list | tuple):
        raise ScenarioError("city inventories must be an array")
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
            "revenue_sources",
            "neighborhoods",
            "place_assets",
            "people",
            "households",
            "organizations",
            "sector_market_balances",
            "inventories",
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
            "revenue_sources": _dataclass_from_mapping(
                CityRevenueSources,
                revenue_sources_data,
                "city revenue_sources",
            ),
            "neighborhoods": neighborhoods,
            "place_assets": place_assets,
            "people": _people_from_sequence(people_data, "city people"),
            "households": _households_from_sequence(households_data, "city households"),
            "organizations": _organizations_from_sequence(
                organizations_data,
                "city organizations",
            ),
            "sector_market_balances": _sector_market_balances_from_sequence(
                sector_market_balances_data,
                "city sector_market_balances",
            ),
            "inventories": _inventories_from_sequence(
                inventories_data,
                "city inventories",
            ),
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
        zoning_data = value.get("zoning", {})
        if not isinstance(zoning_data, dict):
            raise ScenarioError(f"neighborhood {key} zoning must be an object")
        place_assets_data = value.get("place_assets", ())
        if not isinstance(place_assets_data, list | tuple):
            raise ScenarioError(f"neighborhood {key} place_assets must be an array")
        neighborhood_data = {
            field_key: field_value
            for field_key, field_value in value.items()
            if field_key not in {"housing_stock", "housing_assistance", "zoning", "place_assets"}
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
                "zoning": _zoning_envelope_from_mapping(
                    zoning_data,
                    f"neighborhood {key} zoning",
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


def _zoning_envelope_from_mapping(data: dict[str, Any], label: str) -> ZoningEnvelope:
    zoning_data = dict(data)
    _tupleize(zoning_data, ("allowed_uses", "overlay_tags", "special_permit_uses"))
    return _dataclass_from_mapping(ZoningEnvelope, zoning_data, label)


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


def _people_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[PersonAgent, ...]:
    people: list[PersonAgent] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        person_data = dict(value)
        _tupleize(
            person_data,
            ("parent_ids", "health_conditions", "debts", "assets", "notes"),
        )
        person_data["identity"] = _cultural_identity_from_mapping(
            person_data.get("identity"),
            f"{item_label}.identity",
        )
        person_data["language_profile"] = _language_profile_from_mapping(
            person_data.get("language_profile"),
            f"{item_label}.language_profile",
        )
        person_data["adoption"] = _adoption_identity_from_mapping(
            person_data.get("adoption"),
            f"{item_label}.adoption",
        )
        person_data["education_history"] = _education_history_from_mapping(
            person_data.get("education_history"),
            f"{item_label}.education_history",
        )
        person_data["employment_history"] = _employment_history_from_sequence(
            person_data.get("employment_history", ()),
            f"{item_label}.employment_history",
        )
        people.append(_dataclass_from_mapping(PersonAgent, person_data, item_label))
    return tuple(people)


def _cultural_identity_from_mapping(
    data: dict[str, Any] | None,
    label: str,
) -> CulturalIdentity:
    if data is None:
        return CulturalIdentity()
    identity_data = dict(data)
    _tupleize(identity_data, ("ethnicities", "cultures", "languages"))
    affiliations_data = identity_data.get("affiliations", ())
    if not isinstance(affiliations_data, list | tuple):
        raise ScenarioError(f"{label}.affiliations must be an array")
    identity_data["affiliations"] = tuple(
        _cultural_affiliation_from_mapping(value, f"{label}.affiliations[{index}]")
        for index, value in enumerate(affiliations_data)
    )
    return _dataclass_from_mapping(CulturalIdentity, identity_data, label)


def _cultural_affiliation_from_mapping(data: Any, label: str) -> CulturalAffiliation:
    if not isinstance(data, dict):
        raise ScenarioError(f"{label} must be an object")
    affiliation_data = dict(data)
    _tupleize(affiliation_data, ("tags",))
    return _dataclass_from_mapping(CulturalAffiliation, affiliation_data, label)


def _language_profile_from_mapping(
    data: dict[str, Any] | None,
    label: str,
) -> LanguageProfile:
    if data is None:
        return LanguageProfile()
    if not isinstance(data, dict):
        raise ScenarioError(f"{label} must be an object")
    profile_data = dict(data)
    _tupleize(profile_data, ("household_languages",))
    skills_data = profile_data.get("skills", ())
    if not isinstance(skills_data, list | tuple):
        raise ScenarioError(f"{label}.skills must be an array")
    profile_data["skills"] = tuple(
        _language_skill_from_mapping(value, f"{label}.skills[{index}]")
        for index, value in enumerate(skills_data)
    )
    return _dataclass_from_mapping(LanguageProfile, profile_data, label)


def _language_skill_from_mapping(data: Any, label: str) -> LanguageSkill:
    if not isinstance(data, dict):
        raise ScenarioError(f"{label} must be an object")
    skill_data = dict(data)
    _tupleize(skill_data, ("learning_contexts",))
    return _dataclass_from_mapping(LanguageSkill, skill_data, label)


def _adoption_identity_from_mapping(
    data: dict[str, Any] | None,
    label: str,
) -> AdoptionIdentity:
    if data is None:
        return AdoptionIdentity()
    adoption_data = dict(data)
    _tupleize(
        adoption_data,
        (
            "birth_parent_ethnicities",
            "birth_parent_cultures",
            "adoptive_parent_ethnicities",
            "adoptive_parent_cultures",
            "raised_cultures",
        ),
    )
    return _dataclass_from_mapping(AdoptionIdentity, adoption_data, label)


def _education_history_from_mapping(
    data: dict[str, Any] | None,
    label: str,
) -> EducationHistory:
    if data is None:
        return EducationHistory()
    history_data = dict(data)
    _tupleize(
        history_data,
        (
            "daycare_ids",
            "grade_school_ids",
            "high_school_ids",
            "college_ids",
            "trade_school_ids",
            "masters_university_ids",
            "phd_university_ids",
        ),
    )
    graduations_data = history_data.get("graduations", ())
    if not isinstance(graduations_data, list | tuple):
        raise ScenarioError(f"{label}.graduations must be an array")
    history_data["graduations"] = tuple(
        _education_completion_from_mapping(value, f"{label}.graduations[{index}]")
        for index, value in enumerate(graduations_data)
    )
    return _dataclass_from_mapping(EducationHistory, history_data, label)


def _education_completion_from_mapping(
    data: Any,
    label: str,
) -> EducationCompletion:
    if not isinstance(data, dict):
        raise ScenarioError(f"{label} must be an object")
    completion_data = dict(data)
    _tupleize(completion_data, ("skills",))
    return _dataclass_from_mapping(EducationCompletion, completion_data, label)


def _employment_history_from_sequence(
    data: Any,
    label: str,
) -> tuple[EmploymentRecord, ...]:
    if not isinstance(data, list | tuple):
        raise ScenarioError(f"{label} must be an array")
    records: list[EmploymentRecord] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        record_data = dict(value)
        _tupleize(record_data, ("skills_used",))
        records.append(_dataclass_from_mapping(EmploymentRecord, record_data, item_label))
    return tuple(records)


def _households_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[HouseholdAgent, ...]:
    households: list[HouseholdAgent] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        household_data = dict(value)
        _tupleize(
            household_data,
            ("member_ids", "household_languages", "debts", "assets", "notes"),
        )
        households.append(_dataclass_from_mapping(HouseholdAgent, household_data, item_label))
    return tuple(households)


def _organizations_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[OrganizationAgent, ...]:
    organizations: list[OrganizationAgent] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        organization_data = dict(value)
        _tupleize(
            organization_data,
            ("owner_ids", "employee_ids", "customer_types", "notes"),
        )
        organization_data["service_languages"] = _service_languages_from_sequence(
            organization_data.get("service_languages", ()),
            f"{item_label}.service_languages",
        )
        organizations.append(
            _dataclass_from_mapping(OrganizationAgent, organization_data, item_label)
        )
    return tuple(organizations)


def _service_languages_from_sequence(
    data: Any,
    label: str,
) -> tuple[ServiceLanguage, ...]:
    if not isinstance(data, list | tuple):
        raise ScenarioError(f"{label} must be an array")
    service_languages: list[ServiceLanguage] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        language_data = dict(value)
        _tupleize(language_data, ("tags",))
        service_languages.append(
            _dataclass_from_mapping(ServiceLanguage, language_data, item_label)
        )
    return tuple(service_languages)


def _sector_market_balances_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[SectorMarketBalance, ...]:
    balances: list[SectorMarketBalance] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        balance_data = dict(value)
        _tupleize(balance_data, ("notes",))
        balances.append(_dataclass_from_mapping(SectorMarketBalance, balance_data, item_label))
    return tuple(balances)


def _inventories_from_sequence(
    data: list[Any] | tuple[Any, ...],
    label: str,
) -> tuple[InventoryState, ...]:
    inventories: list[InventoryState] = []
    for index, value in enumerate(data):
        item_label = f"{label}[{index}]"
        if not isinstance(value, dict):
            raise ScenarioError(f"{item_label} must be an object")
        inventory_data = dict(value)
        _tupleize(inventory_data, ("notes",))
        inventories.append(_dataclass_from_mapping(InventoryState, inventory_data, item_label))
    return tuple(inventories)


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
