import json

from city_simulator import CityPolicy, SyntheticGroupProfile, generate_synthetic_city
from city_simulator.model import advance_year
from city_simulator.scenario import load_city, save_city
from city_simulator.synthetic_city import synthetic_group_profiles_from_mapping


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
