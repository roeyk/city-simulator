import json
from itertools import repeat

import pytest

from city_simulator.starter import (
    DEFAULT_AGE_MIX,
    _prompt_percent_mix,
    _resolve_auto_percentages,
    custom_city_from_percentages,
    prompt_for_starter_city,
    starter_city,
    write_starter_city,
)


def test_starter_city_can_scale_population():
    city = starter_city("balanced", population=250_000)

    assert city.population == 250_000
    assert city.demographics.total == pytest.approx(250_000)


def test_write_starter_city_creates_json(tmp_path):
    path = tmp_path / "new-city.json"

    city = write_starter_city(path, "stressed", population=80_000)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["population"] == 80_000
    assert data["budget"] == city.budget


def test_unknown_starter_preset_is_rejected():
    with pytest.raises(ValueError, match="unknown city preset"):
        starter_city("unknown")


def test_custom_city_from_percentages_builds_population_profile():
    city = custom_city_from_percentages(
        population=1_000,
        age_mix={"under_18": 20, "age_18_34": 30, "age_35_64": 35, "age_65_plus": 15},
        race_mix={"a": 50, "b": 50},
        sex_mix={"female": 50, "male": 50},
        orientation_mix={"straight": 90, "lesbian_gay_bisexual": 10},
        nationality_mix={"domestic": 80, "foreign": 20},
        religion_mix={"unaffiliated": 50, "christian": 40, "other": 10},
        religiosity_mix={
            "unaffiliated": {"low": 90, "moderate": 10, "high": 0},
            "christian": {"low": 20, "moderate": 50, "high": 30},
            "other": {"low": 30, "moderate": 40, "high": 30},
        },
        education_mix={"hs": 40, "college": 60},
        literacy_age_mix={
            "under_18": {"literate": 90, "limited_literacy": 10},
            "age_18_34": {"literate": 98, "limited_literacy": 2},
            "age_35_64": {"literate": 96, "limited_literacy": 4},
            "age_65_plus": {"literate": 92, "limited_literacy": 8},
        },
        graduation_age_mix={
            "under_18": {
                "not_yet_applicable": 60,
                "not_graduated": 30,
                "high_school_or_equivalent": 10,
                "college_or_higher": 0,
            },
            "age_18_34": {
                "not_yet_applicable": 0,
                "not_graduated": 8,
                "high_school_or_equivalent": 52,
                "college_or_higher": 40,
            },
            "age_35_64": {
                "not_yet_applicable": 0,
                "not_graduated": 10,
                "high_school_or_equivalent": 55,
                "college_or_higher": 35,
            },
            "age_65_plus": {
                "not_yet_applicable": 0,
                "not_graduated": 20,
                "high_school_or_equivalent": 55,
                "college_or_higher": 25,
            },
        },
        income_mix={"low": 30, "middle": 50, "high": 20},
        age_income_mix={
            "under_18": {"low": 60, "middle": 35, "high": 5},
            "age_18_34": {"low": 20, "middle": 40, "high": 40},
            "age_35_64": {"low": 25, "middle": 55, "high": 20},
            "age_65_plus": {"low": 45, "middle": 45, "high": 10},
        },
        workforce_mix={
            "blue_collar": 20,
            "white_collar": 40,
            "pink_collar": 20,
            "public_sector": 15,
            "informal_or_other": 5,
        },
        adult_family={"married": 45, "divorced": 12, "has_children": 40},
        area_square_miles=10,
        terrain_mix={"land": 70, "water": 10, "forest": 20},
        development_mix={"developed": 40, "undeveloped": 60},
        civic_assets={"schools": 2, "neighborhoods": 4},
    )

    assert city.demographics.children == 200
    assert city.demographics.working_age == 650
    assert city.demographics.seniors == 150
    assert city.population_profile["adult_family_count"]["married"] == 360
    assert city.population_profile["age_income_count"]["age_18_34"]["high"] == 120
    assert city.population_profile["age_income_count"]["age_65_plus"]["high"] == 15
    assert city.population_profile["workforce_count"]["white_collar"] == 320
    assert city.population_profile["orientation_count"]["lesbian_gay_bisexual"] == 100
    assert city.population_profile["religion_count"]["christian"] == 400
    assert city.population_profile["religiosity_count"]["christian"]["high"] == 120
    assert city.population_profile["literacy_age_count"]["under_18"]["limited_literacy"] == 20
    assert city.population_profile["graduation_age_count"]["age_18_34"]["college_or_higher"] == 120
    assert city.cohort_profiles["age"]["income_count"]["age_18_34"]["high"] == 120
    assert city.cohort_profiles["religion"]["religiosity_count"]["christian"]["high"] == 120
    assert city.cohort_profiles["workforce"]["category_count"]["white_collar"] == 320
    assert city.physical_profile["population_density_per_square_mile"] == 100
    assert city.physical_profile["terrain_square_miles"]["forest"] == 2
    assert city.civic_assets["schools"] == 2


def test_prompt_for_starter_city_accepts_defaults():
    answers = repeat("")

    city = prompt_for_starter_city(lambda _prompt: next(answers), lambda _message: None)

    assert city.population == 100_000
    assert city.population_profile["age_percent"]["under_18"] == 18.5
    assert city.physical_profile["area_square_miles"] == 55
    assert city.civic_assets["schools"] == 42


def test_prompt_for_starter_city_asks_percentages_one_at_a_time():
    prompts: list[str] = []
    answers = iter(["1000"])
    blank_answers = repeat("")

    def input_func(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers, next(blank_answers))

    city = prompt_for_starter_city(input_func, lambda _message: None)

    assert city.population_profile["age_percent"]["age_65_plus"] == 19.5
    assert city.population_profile["race_percent"]["multiracial_or_other"] == 6
    assert city.population_profile["sex_percent"]["male"] == 49
    assert city.population_profile["orientation_percent"]["lesbian_gay_bisexual"] == 10
    assert city.population_profile["age_income_percent"]["age_18_34"]["high"] == 18
    assert city.population_profile["workforce_percent"]["white_collar"] == 38
    assert any("under_18" in prompt for prompt in prompts)
    assert any("age_18_34" in prompt for prompt in prompts)
    assert any("remaining" in prompt for prompt in prompts)


def test_blank_percentage_gets_remainder_after_explicit_entries():
    values = {"a": 20.0, "b": None, "c": 30.0, "d": 10.0}
    defaults = {"a": 25.0, "b": 25.0, "c": 25.0, "d": 25.0}

    resolved = _resolve_auto_percentages(values, defaults, "test mix")

    assert resolved == {"a": 20.0, "b": 40.0, "c": 30.0, "d": 10.0}


def test_blank_percentage_prompts_show_prior_default_allocation():
    prompts: list[str] = []
    answers = iter(["", "", "", ""])

    def input_func(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    values = _prompt_percent_mix(input_func, "age groups", DEFAULT_AGE_MIX)

    assert values["age_65_plus"] == 19.5
    assert "under_18 [18.5; remaining 100]" in prompts[0]
    assert "age_18_34 [22; remaining 81.5]" in prompts[1]
    assert "age_35_64 [40; remaining 59.5]" in prompts[2]
    assert "age_65_plus [19.5; remaining 19.5]" in prompts[3]


def test_age_income_table_distinguishes_young_rich_from_old_rich():
    young_rich = custom_city_from_percentages(
        population=1_000,
        age_mix={"under_18": 20, "age_18_34": 40, "age_35_64": 30, "age_65_plus": 10},
        race_mix={"all": 100},
        sex_mix={"all": 100},
        orientation_mix={"all": 100},
        nationality_mix={"all": 100},
        religion_mix={"all": 100},
        religiosity_mix={"all": {"low": 20, "moderate": 50, "high": 30}},
        education_mix={"all": 100},
        literacy_age_mix={
            "under_18": {"literate": 90, "limited_literacy": 10},
            "age_18_34": {"literate": 95, "limited_literacy": 5},
            "age_35_64": {"literate": 95, "limited_literacy": 5},
            "age_65_plus": {"literate": 90, "limited_literacy": 10},
        },
        graduation_age_mix={
            "under_18": {"not_yet_applicable": 100},
            "age_18_34": {"high_school_or_equivalent": 60, "college_or_higher": 40},
            "age_35_64": {"high_school_or_equivalent": 60, "college_or_higher": 40},
            "age_65_plus": {"high_school_or_equivalent": 70, "college_or_higher": 30},
        },
        income_mix={"low": 30, "middle": 40, "high": 30},
        age_income_mix={
            "under_18": {"low": 50, "middle": 45, "high": 5},
            "age_18_34": {"low": 10, "middle": 30, "high": 60},
            "age_35_64": {"low": 30, "middle": 50, "high": 20},
            "age_65_plus": {"low": 45, "middle": 45, "high": 10},
        },
        workforce_mix={"all": 100},
        adult_family={"married": 50},
    )
    old_rich = custom_city_from_percentages(
        population=1_000,
        age_mix={"under_18": 20, "age_18_34": 40, "age_35_64": 30, "age_65_plus": 10},
        race_mix={"all": 100},
        sex_mix={"all": 100},
        orientation_mix={"all": 100},
        nationality_mix={"all": 100},
        religion_mix={"all": 100},
        religiosity_mix={"all": {"low": 20, "moderate": 50, "high": 30}},
        education_mix={"all": 100},
        literacy_age_mix={
            "under_18": {"literate": 90, "limited_literacy": 10},
            "age_18_34": {"literate": 95, "limited_literacy": 5},
            "age_35_64": {"literate": 95, "limited_literacy": 5},
            "age_65_plus": {"literate": 90, "limited_literacy": 10},
        },
        graduation_age_mix={
            "under_18": {"not_yet_applicable": 100},
            "age_18_34": {"high_school_or_equivalent": 60, "college_or_higher": 40},
            "age_35_64": {"high_school_or_equivalent": 60, "college_or_higher": 40},
            "age_65_plus": {"high_school_or_equivalent": 70, "college_or_higher": 30},
        },
        income_mix={"low": 30, "middle": 40, "high": 30},
        age_income_mix={
            "under_18": {"low": 50, "middle": 45, "high": 5},
            "age_18_34": {"low": 35, "middle": 55, "high": 10},
            "age_35_64": {"low": 30, "middle": 50, "high": 20},
            "age_65_plus": {"low": 10, "middle": 30, "high": 60},
        },
        workforce_mix={"all": 100},
        adult_family={"married": 50},
    )

    assert young_rich.population_profile["age_income_count"]["age_18_34"]["high"] == 240
    assert old_rich.population_profile["age_income_count"]["age_18_34"]["high"] == 40
    assert young_rich.population_profile["age_income_count"]["age_65_plus"]["high"] == 10
    assert old_rich.population_profile["age_income_count"]["age_65_plus"]["high"] == 60
