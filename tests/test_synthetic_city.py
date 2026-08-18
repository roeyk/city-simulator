import json

from city_simulator import CityPolicy, generate_synthetic_city
from city_simulator.model import advance_year
from city_simulator.scenario import load_city, save_city


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
