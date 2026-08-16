from city_simulator import HouseholdAgent, PersonAgent, living_conditions_for


def test_dependent_inherits_living_conditions_from_household():
    household = HouseholdAgent(
        "hernandez",
        member_ids=("renee-hernandez",),
        income_band="middle",
        tenure="owner",
        neighborhood="summer_crescent_boulevard",
        housing_status="single-family house",
    )
    child = PersonAgent(
        "renee-hernandez",
        household_id="hernandez",
        age=5,
        income_band="",
        employment_status="student",
    )

    conditions = living_conditions_for(child, household)

    assert conditions.household_id == "hernandez"
    assert conditions.income_band == "middle"
    assert conditions.tenure == "owner"
    assert conditions.neighborhood == "summer_crescent_boulevard"
    assert conditions.housing_status == "single-family house"


def test_person_living_condition_overrides_allow_split_household_cases():
    household = HouseholdAgent(
        "parent-a-home",
        member_ids=("child-1",),
        income_band="middle",
        tenure="owner",
        neighborhood="village_hills",
        housing_status="single-family house",
    )
    child = PersonAgent(
        "child-1",
        household_id="parent-a-home",
        age=10,
        income_band="",
        neighborhood="summer_crescent_boulevard",
        housing_status="apartment",
    )

    conditions = living_conditions_for(child, household)

    assert conditions.income_band == "middle"
    assert conditions.neighborhood == "summer_crescent_boulevard"
    assert conditions.housing_status == "apartment"
