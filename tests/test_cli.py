import json

import pytest

from city_simulator.cli import main


@pytest.fixture(autouse=True)
def isolated_data_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))


def test_table_cli_outputs_years(capsys):
    exit_code = main(["--years", "2"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Year" in output
    assert "Population" in output
    assert "Unemp" in output
    assert "Issues" in output
    assert "Overcome" in output
    assert "1" in output
    assert "2" in output


def test_json_cli_outputs_valid_json(capsys):
    exit_code = main(["--years", "1", "--format", "json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"year": 1' in output
    assert '"population_delta"' in output
    assert '"demographics"' in output
    assert '"labor_force"' in output
    assert '"sentiment_signals"' in output
    assert '"active_issues"' in output


def test_cli_compares_multiple_scenarios(tmp_path, capsys):
    city = tmp_path / "city.json"
    city.write_text('{"population": 100000}', encoding="utf-8")
    housing = tmp_path / "housing.json"
    housing.write_text(
        '{"name": "housing", "years": 2, "policy": {"housing_investment": 70000000}}',
        encoding="utf-8",
    )
    business = tmp_path / "business.json"
    business.write_text(
        '{"name": "business", "years": 2, "policy": {"business_support": 60000000}}',
        encoding="utf-8",
    )

    exit_code = main(["--city", str(city), "--scenario", str(housing), "--scenario", str(business)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Scenario" in output
    assert "Unemp" in output
    assert "housing" in output
    assert "business" in output


def test_cli_accepts_migration_and_restriction_flags(capsys):
    exit_code = main(
        [
            "--years",
            "1",
            "--citizen-influx-rate",
            "0.02",
            "--citizen-outflux-rate",
            "0.001",
            "--zoning-restrictiveness",
            "0.1",
            "--permitting-speed",
            "0.9",
            "--development-restriction",
            "0.05",
        ]
    )

    assert exit_code == 0
    assert "Scenario: manual policy" in capsys.readouterr().out


def test_cli_outputs_citizen_stories(capsys):
    exit_code = main(["--years", "1", "--citizen-stories", "2"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Citizen Stories" in output
    assert "citizen-0-0" in output


def test_cli_reports_invalid_scenario(tmp_path, capsys):
    scenario = tmp_path / "bad.json"
    scenario.write_text('{"policy": {"unknown": 1}}', encoding="utf-8")

    exit_code = main(["--scenario", str(scenario)])

    assert exit_code == 2
    assert "unknown policy fields" in capsys.readouterr().out


def test_cli_init_city_writes_starter_city(tmp_path, capsys):
    path = tmp_path / "starter.json"

    exit_code = main(["init-city", str(path), "--preset", "growing", "--population", "200000"])

    assert exit_code == 0
    assert path.exists()
    assert "Wrote growing city" in capsys.readouterr().out


def test_cli_init_city_name_uses_data_home(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))

    exit_code = main(["init-city", "starter", "--preset", "balanced"])

    assert exit_code == 0
    assert (tmp_path / "cities" / "starter.json").exists()
    assert str(tmp_path / "cities" / "starter.json") in capsys.readouterr().out


def test_cli_init_city_wizard_writes_custom_city(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    answers = iter(["1000", *([""] * 120)])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    exit_code = main(["init-city", "wizard", "--wizard"])

    assert exit_code == 0
    path = tmp_path / "cities" / "wizard.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["population"] == 1000
    assert "population_profile" in data
    assert "physical_profile" in data
    assert "civic_assets" in data
    assert "Wrote balanced city" in capsys.readouterr().out


def test_cli_prompts_for_saved_city_when_city_not_supplied(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    main(["init-city", "alpha", "--population", "1000"])
    main(["init-city", "beta", "--population", "2000"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "2")

    exit_code = main(["--years", "1"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Saved cities:" in output
    assert "beta" in output
    assert "2,125" in output


def test_cli_play_advances_and_saves_turns(tmp_path, monkeypatch, capsys):
    main(["init-city", "alpha", "--population", "1000"])
    answers = iter(["turn", "status", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    exit_code = main(["play", "--city", "alpha"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Continuing alpha" in output
    assert "Saved alpha" in output
    data = json.loads((tmp_path / "cities" / "alpha.json").read_text(encoding="utf-8"))
    assert data["year"] == 1
