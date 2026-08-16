from city_simulator import (
    FamilyGenerationSpec,
    generate_family_agents,
    generate_family_population,
)


def test_generate_family_agents_uses_heritage_name_bank():
    family = generate_family_agents(
        "hispanic",
        household_index=0,
        adults=2,
        children=2,
        income_band="middle",
        neighborhood="summer_crescent_boulevard",
    )

    assert family.household.agent_id == "hernandez"
    assert family.household.member_ids == (
        "juan-hernandez-1",
        "louise-hernandez-2",
        "renee-hernandez-3",
        "jose-hernandez-4",
    )
    assert [person.display_name for person in family.people] == [
        "Juan Hernandez",
        "Louise Hernandez",
        "Renee Hernandez",
        "Jose Hernandez",
    ]
    assert all(person.household_id == "hernandez" for person in family.people)
    assert all(person.neighborhood == "summer_crescent_boulevard" for person in family.people)
    assert family.support_need == 4
    assert family.support_capacity == 6
    assert family.support_gap == 0
    assert family.household.notes == ()


def test_generate_family_agents_is_deterministic_by_heritage_and_index():
    first = generate_family_agents("jewish", household_index=2, adults=1, children=1)
    second = generate_family_agents("jewish", household_index=2, adults=1, children=1)

    assert first == second
    assert first.household.agent_id == "levine"
    assert first.people[0].display_name == "Ari Levine"


def test_generate_family_agents_marks_retail_parent_under_housing_strain():
    family = generate_family_agents(
        "anglo",
        household_index=1,
        adults=1,
        children=2,
        income_band="low",
        housing_cost_band="high",
        adult_roles=("retail salesman",),
    )

    assert family.people[0].role == "retail salesman"
    assert family.support_need == 4
    assert family.support_capacity == 2
    assert family.support_gap == 2
    assert family.household.notes == (
        "financial strain: high housing cost exceeds adult earning support capacity",
    )


def test_generate_family_agents_credits_lower_cost_housing():
    family = generate_family_agents(
        "anglo",
        household_index=1,
        adults=1,
        children=1,
        income_band="low",
        housing_cost_band="low",
        adult_roles=("retail salesman",),
    )

    assert family.support_need == 1.5
    assert family.support_capacity == 2
    assert family.support_gap == 0
    assert family.household.notes == ()


def test_generate_family_population_returns_families_before_people():
    population = generate_family_population(
        (
            FamilyGenerationSpec(
                "hispanic",
                household_index=0,
                adults=2,
                children=2,
                income_band="middle",
            ),
            FamilyGenerationSpec(
                "anglo",
                household_index=1,
                adults=1,
                children=1,
                income_band="low",
                adult_roles=("retail salesman",),
            ),
        )
    )

    assert [family.household.agent_id for family in population.families] == [
        "hernandez",
        "harcourt",
    ]
    assert [household.agent_id for household in population.households] == [
        "hernandez",
        "harcourt",
    ]
    assert [person.household_id for person in population.people] == [
        "hernandez",
        "hernandez",
        "hernandez",
        "hernandez",
        "harcourt",
        "harcourt",
    ]


def test_generate_family_agents_rejects_unknown_heritage():
    try:
        generate_family_agents("unknown")
    except ValueError as exc:
        assert "unknown heritage" in str(exc)
    else:
        raise AssertionError("unknown heritage should be rejected")


def test_generate_family_agents_rejects_invalid_family_sizes(
):
    invalid_sizes = (
        (-1, 0, "non-negative"),
        (0, -1, "non-negative"),
        (0, 0, "at least one person"),
    )
    for adults, children, match in invalid_sizes:
        try:
            generate_family_agents("anglo", adults=adults, children=children)
        except ValueError as exc:
            assert match in str(exc)
        else:
            raise AssertionError("invalid family size should be rejected")


def test_generate_family_agents_rejects_invalid_weight():
    try:
        generate_family_agents("anglo", weight=0)
    except ValueError as exc:
        assert "weight must be positive" in str(exc)
    else:
        raise AssertionError("invalid weight should be rejected")


def test_generate_family_agents_rejects_invalid_housing_cost_band():
    try:
        generate_family_agents("anglo", housing_cost_band="luxury")
    except ValueError as exc:
        assert "housing_cost_band" in str(exc)
    else:
        raise AssertionError("invalid housing cost band should be rejected")
