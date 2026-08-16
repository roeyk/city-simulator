from city_simulator.storage import (
    city_path,
    ensure_data_dirs,
    saved_cities,
    scenario_path,
)


def test_named_paths_use_data_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))

    assert city_path("my-city") == tmp_path / "cities" / "my-city.json"
    assert scenario_path("growth.json") == tmp_path / "scenarios" / "growth.json"


def test_explicit_paths_are_preserved(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path / "home"))
    explicit = tmp_path / "custom.json"

    assert city_path(explicit) == explicit


def test_ensure_data_dirs_creates_expected_directories(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))

    ensure_data_dirs()

    assert (tmp_path / "cities").is_dir()
    assert (tmp_path / "scenarios").is_dir()
    assert (tmp_path / "reports").is_dir()


def test_saved_cities_lists_city_json_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    ensure_data_dirs()
    (tmp_path / "cities" / "b.json").write_text("{}", encoding="utf-8")
    (tmp_path / "cities" / "a.json").write_text("{}", encoding="utf-8")

    assert [path.stem for path in saved_cities()] == ["a", "b"]
