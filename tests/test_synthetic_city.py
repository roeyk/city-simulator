import json
from pathlib import Path

from city_simulator import CityPolicy, SyntheticGroupProfile, generate_synthetic_city
from city_simulator.model import advance_year
from city_simulator.scenario import load_city, save_city
from city_simulator.synthetic_city import (
    SyntheticHouseholdMemberProfile,
    SyntheticMixedHouseholdProfile,
    synthetic_group_profiles_from_mapping,
    synthetic_population_profile_from_mapping,
)

EXAMPLE_SYNTHETIC_PROFILE_DIR = (
    Path(__file__).resolve().parents[1] / "examples" / "synthetic-profiles"
)


def test_generate_synthetic_city_creates_testable_city_surface(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))

    city = generate_synthetic_city(12)
    path = save_city("synthetic-test", city)
    loaded = load_city(path)

    assert loaded.population == 12
    assert len(loaded.people) == 12
    assert loaded.demographics.total == 12
    assert loaded.households
    assert any(organization.agent_id == "grocery-1" for organization in loaded.organizations)
    assert loaded.sector_market_balances
    assert loaded.inventories
    assert any(inventory.holder_type == "household" for inventory in loaded.inventories)
    assert any(inventory.holder_id == "grocery-1" for inventory in loaded.inventories)


def test_generate_synthetic_city_is_deterministic():
    first = generate_synthetic_city(15)
    second = generate_synthetic_city(15)

    assert first.people == second.people
    assert first.households == second.households
    assert first.organizations == second.organizations
    assert first.inventories == second.inventories
    assert first.sector_market_balances == second.sector_market_balances


def test_generate_synthetic_city_uses_unique_person_and_household_ids():
    city = generate_synthetic_city(
        170,
        group_profiles=(
            SyntheticGroupProfile(
                heritage="american",
                population_share=100,
                income_bands=(("middle", 100.0),),
                job_pools=(("private_service", 100.0),),
            ),
            SyntheticGroupProfile(
                heritage="latino",
                population_share=70,
                income_bands=(("low", 100.0),),
                job_pools=(("city_service", 100.0),),
            ),
        ),
    )

    person_ids = [person.agent_id for person in city.people]
    household_ids = [household.agent_id for household in city.households]
    household_ids_by_person = {person.household_id for person in city.people}

    assert len(person_ids) == len(set(person_ids))
    assert len(household_ids) == len(set(household_ids))
    assert household_ids_by_person <= set(household_ids)
    assert all(person_id.startswith("person-") for person_id in person_ids)
    assert all(household_id.startswith("household-") for household_id in household_ids)


def test_generate_synthetic_city_uses_group_population_income_and_vocation_profiles():
    city = generate_synthetic_city(
        20,
        group_profiles=(
            SyntheticGroupProfile(
                heritage="anglo",
                population_share=60,
                income_bands=(("high", 1.0),),
                job_pools=(("business_owner", 1.0),),
            ),
            SyntheticGroupProfile(
                heritage="hispanic",
                population_share=40,
                income_bands=(("low", 1.0),),
                job_pools=(("city_service", 1.0),),
            ),
        ),
    )

    people_by_group = {
        "anglo": tuple(person for person in city.people if "anglo" in person.identity.ethnicities),
        "hispanic": tuple(
            person for person in city.people if "hispanic" in person.identity.ethnicities
        ),
    }
    household_by_id = {household.agent_id: household for household in city.households}
    anglo_households = {
        household_by_id[person.household_id]
        for person in people_by_group["anglo"]
    }
    hispanic_households = {
        household_by_id[person.household_id]
        for person in people_by_group["hispanic"]
    }

    assert len(people_by_group["anglo"]) == 12
    assert len(people_by_group["hispanic"]) == 8
    assert {person.income_band for person in people_by_group["anglo"]} == {"high"}
    assert {person.income_band for person in people_by_group["hispanic"]} == {"low"}
    assert {household.income_band for household in anglo_households} == {"high"}
    assert {household.income_band for household in hispanic_households} == {"low"}
    assert any(
        person.employment_status == "business_owner"
        for person in people_by_group["anglo"]
        if person.is_working_age
    )
    assert any(
        person.role in {"firefighter", "police officer", "waterworks operator"}
        for person in people_by_group["hispanic"]
        if person.is_working_age
    )


def test_generate_synthetic_city_supports_explicit_mixed_households():
    city = generate_synthetic_city(
        8,
        group_profiles=(
            SyntheticGroupProfile(
                heritage="american",
                population_share=100,
                income_bands=(("middle", 100.0),),
                job_pools=(("private_service", 100.0),),
            ),
        ),
        mixed_households=(
            SyntheticMixedHouseholdProfile(
                members=(
                    SyntheticHouseholdMemberProfile("american", "high", 42),
                    SyntheticHouseholdMemberProfile("latino", "low", 39),
                    SyntheticHouseholdMemberProfile("black_american", "middle", 10),
                ),
                count=1,
                job_pools=(("private_service", 100.0),),
            ),
        ),
    )

    mixed_household = city.households[0]
    mixed_members = tuple(person for person in city.people if person.household_id == mixed_household.agent_id)

    assert mixed_household.income_band == "middle"
    assert {person.identity.ethnicities[0] for person in mixed_members} == {
        "american",
        "black_american",
        "latino",
    }
    assert {person.income_band for person in mixed_members} == {"high", "low", "middle"}
    assert any(person.current_school_id == "school-elementary-1" for person in mixed_members)


def test_generate_synthetic_city_assigns_schools_workplaces_and_employee_ids():
    city = generate_synthetic_city(
        40,
        group_profiles=(
            SyntheticGroupProfile(
                heritage="american",
                population_share=100,
                income_bands=(("middle", 100.0),),
                job_pools=(("business_owner", 35.0), ("private_service", 65.0)),
            ),
        ),
    )

    organizations_by_id = {organization.agent_id: organization for organization in city.organizations}
    business_organizations = tuple(
        organization
        for organization in city.organizations
        if organization.organization_type == "business"
    )
    school_ids = {
        organization.agent_id
        for organization in city.organizations
        if organization.sector == "education"
    }
    students = tuple(person for person in city.people if person.current_school_id)
    workers = tuple(person for person in city.people if person.workplace_id)

    assert {"school-elementary-1", "school-high-1", "college-community-1"} <= school_ids
    assert {
        "city-hall-1",
        "city-services-1",
        "grocery-1",
        "hospital-1",
        "restaurant-1",
        "warehouse-1",
    } <= set(organizations_by_id)
    assert students
    assert workers
    assert business_organizations
    assert any(len(organization.employee_ids) > 1 for organization in business_organizations)
    assert all(person.current_school_id in school_ids for person in students)
    assert all(person.workplace_id in organizations_by_id for person in workers)


def test_generate_synthetic_city_can_assign_civic_leadership_roles():
    city = generate_synthetic_city(
        80,
        group_profiles=(
            SyntheticGroupProfile(
                heritage="american",
                population_share=100,
                income_bands=(("middle", 70.0), ("high", 30.0)),
                job_pools=(("government", 100.0),),
            ),
        ),
    )

    workplace_by_role = {
        person.role: person.workplace_id
        for person in city.people
        if person.role in {"mayor", "city council member", "city planner"}
    }

    assert workplace_by_role["mayor"] == "mayor-office-1"
    assert workplace_by_role["city council member"] == "city-council-1"
    assert workplace_by_role["city planner"] == "city-planning-1"


def test_synthetic_group_profiles_parse_percent_income_and_vocation_mapping():
    profiles = synthetic_group_profiles_from_mapping(
        {
            "groups": [
                {
                    "ethnicity": "anglo",
                    "percent": 70,
                    "income_bands": {"middle": 80, "high": 20},
                    "vocations": {"private_service": 60, "business_owner": 40},
                },
                {
                    "heritage": "hispanic",
                    "population_share": 30,
                    "income_bands": {"low": 60, "middle": 40},
                    "job_pools": {"city_service": 100},
                },
            ]
        }
    )

    assert profiles[0] == SyntheticGroupProfile(
        heritage="anglo",
        population_share=70,
        income_bands=(("middle", 80.0), ("high", 20.0)),
        job_pools=(("private_service", 60.0), ("business_owner", 40.0)),
    )
    assert profiles[1].heritage == "hispanic"
    assert profiles[1].job_pools == (("city_service", 100.0),)


def test_synthetic_population_profile_parses_mixed_households():
    profile = synthetic_population_profile_from_mapping(
        {
            "groups": [
                {
                    "heritage": "american",
                    "population_share": 100,
                    "income_bands": {"middle": 100},
                }
            ],
            "mixed_households": [
                {
                    "count": 2,
                    "members": [
                        {"heritage": "american", "income_band": "middle", "age": 40},
                        {"ethnicity": "latino", "class": "low", "age": 38},
                    ],
                    "job_pools": {"private_service": 100},
                }
            ],
        }
    )

    assert len(profile.groups) == 1
    assert len(profile.mixed_households) == 1
    assert profile.mixed_households[0].count == 2
    assert profile.mixed_households[0].members[1].heritage == "latino"
    assert profile.mixed_households[0].members[1].income_band == "low"


def test_example_synthetic_profiles_parse_and_generate_cities():
    profile_paths = tuple(sorted(EXAMPLE_SYNTHETIC_PROFILE_DIR.glob("*.json")))

    assert profile_paths
    for profile_path in profile_paths:
        profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
        profiles = synthetic_group_profiles_from_mapping(profile_data)
        city = generate_synthetic_city(40, group_profiles=profiles)

        assert city.population == 40
        assert len(city.people) == 40
        assert city.households
        assert city.sector_market_balances


def test_generate_synthetic_city_emits_supply_and_inventory_signals():
    result = advance_year(generate_synthetic_city(12), CityPolicy())

    assert result.signal_ledger.get("sector_unmet_demand") > 0
    assert result.signal_ledger.get("regional_import_dependency") > 0
    assert result.signal_ledger.get("inventory_stockout_risk") > 0
    assert result.signal_ledger.get("inventory_spoilage_risk") > 0


def test_generate_synthetic_city_rejects_nonpositive_people():
    try:
        generate_synthetic_city(0)
    except ValueError as exc:
        assert "people must be positive" in str(exc)
    else:
        raise AssertionError("nonpositive people count should be rejected")


def test_cli_init_city_can_write_synthetic_city(tmp_path, monkeypatch, capsys):
    from city_simulator.cli import main

    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))

    exit_code = main(["init-city", "synthetic-test", "--synthetic", "--people", "12"])

    data = json.loads((tmp_path / "cities" / "synthetic-test.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert data["population"] == 12
    assert len(data["people"]) == 12
    assert data["sector_market_balances"]
    assert data["inventories"]
    assert "Wrote synthetic city" in capsys.readouterr().out


def test_cli_init_city_can_write_group_profiled_synthetic_city(
    tmp_path,
    monkeypatch,
    capsys,
):
    from city_simulator.cli import main

    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "groups": [
                    {
                        "heritage": "anglo",
                        "population_share": 50,
                        "income_bands": {"high": 100},
                        "job_pools": {"business_owner": 100},
                    },
                    {
                        "heritage": "hispanic",
                        "population_share": 50,
                        "income_bands": {"low": 100},
                        "job_pools": {"city_service": 100},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "init-city",
            "synthetic-profiled",
            "--synthetic",
            "--people",
            "20",
            "--synthetic-profile",
            str(profile_path),
        ]
    )

    data = json.loads((tmp_path / "cities" / "synthetic-profiled.json").read_text())
    ethnicities = [
        person["identity"]["ethnicities"][0]
        for person in data["people"]
    ]
    assert exit_code == 0
    assert ethnicities.count("anglo") == 10
    assert ethnicities.count("hispanic") == 10
    assert "Wrote synthetic city" in capsys.readouterr().out


def test_cli_init_city_can_use_example_synthetic_profile(
    tmp_path,
    monkeypatch,
    capsys,
):
    from city_simulator.cli import main

    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    profile_path = EXAMPLE_SYNTHETIC_PROFILE_DIR / "language-access-stress.json"

    exit_code = main(
        [
            "init-city",
            "language-access-test",
            "--synthetic",
            "--people",
            "40",
            "--synthetic-profile",
            str(profile_path),
        ]
    )

    data = json.loads((tmp_path / "cities" / "language-access-test.json").read_text())
    ethnicities = {
        person["identity"]["ethnicities"][0]
        for person in data["people"]
    }
    assert exit_code == 0
    assert len(data["people"]) == 40
    assert {"mexican", "chinese", "haitian", "ethiopian"}.issubset(ethnicities)
    assert "Wrote synthetic city" in capsys.readouterr().out


def test_cli_init_city_rejects_profile_without_synthetic(
    tmp_path,
    monkeypatch,
    capsys,
):
    from city_simulator.cli import main

    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps({"groups": []}), encoding="utf-8")

    exit_code = main(["init-city", "plain", "--synthetic-profile", str(profile_path)])

    assert exit_code == 2
    assert "--synthetic-profile requires --synthetic" in capsys.readouterr().out
