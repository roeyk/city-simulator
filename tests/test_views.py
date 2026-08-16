from math import isclose

from city_simulator import CityState, Demographics, PopulationStructureView


def test_population_structure_view_derives_from_city_state():
    state = CityState(
        population=200,
        demographics=Demographics(
            children=40,
            working_age=120,
            seniors=40,
            low_income=50,
            middle_income=100,
            high_income=50,
        ),
    )

    view = PopulationStructureView.derive(state)

    assert view.name == "population_structure"
    assert view.source_dependencies == ("population", "demographics")
    assert view.total_population == 200
    assert isclose(view.child_share, 0.2)
    assert isclose(view.working_age_share, 0.6)
    assert isclose(view.senior_share, 0.2)
    assert isclose(view.low_income_share, 0.25)
    assert isclose(view.middle_income_share, 0.5)
    assert isclose(view.high_income_share, 0.25)
    assert isclose(view.dependency_ratio, 80 / 120)


def test_population_structure_view_exports_plain_values():
    view = PopulationStructureView.derive(CityState())

    assert set(view.as_dict()) == {
        "total_population",
        "child_share",
        "working_age_share",
        "senior_share",
        "low_income_share",
        "middle_income_share",
        "high_income_share",
        "dependency_ratio",
    }
