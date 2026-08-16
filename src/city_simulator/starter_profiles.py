from __future__ import annotations

from city_simulator.model import CityState, Demographics

STARTER_PRESETS = {
    "balanced": CityState(),
    "growing": CityState(
        population=145_000,
        demographics=Demographics(
            children=30_000,
            working_age=92_000,
            seniors=23_000,
            low_income=42_000,
            middle_income=75_000,
            high_income=28_000,
        ),
        housing_units=61_000,
        jobs=90_000,
        budget=180_000_000,
        infrastructure=76,
        pollution=42,
        satisfaction=66,
    ),
    "stressed": CityState(
        population=115_000,
        demographics=Demographics(
            children=22_000,
            working_age=70_000,
            seniors=23_000,
            low_income=52_000,
            middle_income=49_000,
            high_income=14_000,
        ),
        housing_units=42_000,
        jobs=58_000,
        budget=-8_000_000,
        infrastructure=49,
        pollution=63,
        satisfaction=41,
    ),
}

DEFAULT_AGE_MIX = {
    "under_18": 18.5,
    "age_18_34": 22.0,
    "age_35_64": 40.0,
    "age_65_plus": 19.5,
}
DEFAULT_RACE_MIX = {
    "white": 45.0,
    "black": 22.0,
    "asian": 9.0,
    "latino": 18.0,
    "multiracial_or_other": 6.0,
}
DEFAULT_SEX_MIX = {
    "female": 51.0,
    "male": 49.0,
}
DEFAULT_ORIENTATION_MIX = {
    "straight": 90.0,
    "lesbian_gay_bisexual": 10.0,
}
DEFAULT_NATIONALITY_MIX = {
    "domestic_born": 82.0,
    "naturalized": 9.0,
    "noncitizen_resident": 9.0,
}
DEFAULT_RELIGION_MIX = {
    "unaffiliated": 35.0,
    "christian": 45.0,
    "muslim": 5.0,
    "jewish": 3.0,
    "hindu": 2.0,
    "buddhist": 2.0,
    "other_religion": 8.0,
}
DEFAULT_RELIGIOSITY_MIX = {
    "low": 35.0,
    "moderate": 45.0,
    "high": 20.0,
}
DEFAULT_LITERACY_MIX = {
    "literate": 96.0,
    "limited_literacy": 4.0,
}
DEFAULT_GRADUATION_MIX = {
    "not_yet_applicable": 15.0,
    "not_graduated": 10.0,
    "high_school_or_equivalent": 45.0,
    "college_or_higher": 30.0,
}
DEFAULT_EDUCATION_MIX = {
    "less_than_high_school": 10.0,
    "high_school": 28.0,
    "some_college": 24.0,
    "bachelors": 25.0,
    "graduate": 13.0,
}
DEFAULT_INCOME_MIX = {
    "low": 34.0,
    "middle": 48.0,
    "high": 18.0,
}
DEFAULT_WORKFORCE_MIX = {
    "blue_collar": 22.0,
    "white_collar": 38.0,
    "pink_collar": 20.0,
    "public_sector": 14.0,
    "informal_or_other": 6.0,
}
DEFAULT_ADULT_FAMILY_STATS = {
    "never_married": 31.0,
    "married": 46.0,
    "divorced": 13.0,
    "widowed": 6.0,
    "second_marriage": 11.0,
    "third_plus_marriage": 3.0,
    "has_children": 42.0,
}
DEFAULT_TERRAIN_MIX = {
    "land": 78.0,
    "water": 6.0,
    "forest": 8.0,
    "desert": 0.0,
    "plains": 8.0,
}
DEFAULT_DEVELOPMENT_MIX = {
    "developed": 45.0,
    "undeveloped": 55.0,
}
DEFAULT_CIVIC_ASSETS = {
    "schools": 42.0,
    "fire_stations": 12.0,
    "police_stations": 7.0,
    "libraries": 9.0,
    "retail_districts": 6.0,
    "industrial_districts": 3.0,
    "office_districts": 4.0,
    "government_districts": 2.0,
    "neighborhoods": 28.0,
}

