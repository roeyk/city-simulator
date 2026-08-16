from math import isclose

from city_simulator import (
    Agent,
    CityState,
    Demographics,
    HouseholdAgent,
    OrganizationAgent,
    PersonAgent,
    PopulationStructureView,
)


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


def test_population_structure_view_can_roll_up_weighted_people():
    people = (
        PersonAgent("child-1", "family-1", age=8, income_band="low", weight=20),
        PersonAgent("worker-1", "family-1", age=36, income_band="middle", weight=50),
        PersonAgent("senior-1", "family-2", age=72, income_band="high", weight=30),
    )

    view = PopulationStructureView.derive_from_people(people)

    assert view.total_population == 100
    assert isclose(view.child_share, 0.2)
    assert isclose(view.working_age_share, 0.5)
    assert isclose(view.senior_share, 0.3)
    assert isclose(view.low_income_share, 0.2)
    assert isclose(view.middle_income_share, 0.5)
    assert isclose(view.high_income_share, 0.3)
    assert isclose(view.dependency_ratio, 1.0)


def test_agent_types_share_identity_and_weight():
    person = PersonAgent("person-1", household_id="household-1", age=34, income_band="middle")
    household = HouseholdAgent(
        "household-1",
        member_ids=("person-1",),
        income_band="middle",
        weight=12,
    )
    organization = OrganizationAgent(
        "org-1",
        organization_type="nonprofit",
        sector="housing",
        weight=3,
    )

    assert isinstance(person, Agent)
    assert isinstance(household, Agent)
    assert isinstance(organization, Agent)
    assert person.weight == 1
    assert household.weight == 12
    assert organization.weight == 3
