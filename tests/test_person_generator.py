from city_simulator import (
    FamilyGenerationSpec,
    eligible_job_template_for,
    generate_family_agents,
    generate_family_population,
    job_template_for,
    trade_school_program_for,
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


def test_adopted_child_keeps_birth_identity_but_uses_raised_culture_name():
    family = generate_family_agents(
        "anglo",
        birth_heritages=("hispanic", "jewish"),
        household_index=0,
        adults=2,
        children=1,
    )

    child = family.people[2]

    assert child.display_name == "Morty Jones"
    assert child.identity.cultures == ("anglo",)
    assert child.adoption.is_adopted
    assert child.adoption.birth_parent_ethnicities == ("hispanic", "jewish")
    assert child.adoption.birth_parent_cultures == ("hispanic", "jewish")
    assert child.adoption.adoptive_parent_ethnicities == ("anglo",)
    assert child.adoption.raised_cultures == ("anglo",)
    assert child.parent_ids == ("dorothy-jones-1", "ron-jones-2")


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
    assert population.organizations == ()


def test_generate_family_agents_draws_city_service_jobs_from_catalog():
    family = generate_family_agents(
        "anglo",
        household_index=0,
        adults=2,
        job_pools=("city_service",),
        adult_education=("high_school",),
        adult_experience_years=(4,),
    )

    assert [person.role for person in family.people] == [
        "firefighter",
        "police officer",
    ]
    assert [person.income_band for person in family.people] == ["middle", "middle"]


def test_generate_family_agents_skips_jobs_with_unmet_prerequisites():
    family = generate_family_agents(
        "anglo",
        household_index=0,
        adults=1,
        job_pools=("government",),
        adult_ages=(22,),
        adult_education=("high_school",),
        adult_experience_years=(2,),
    )

    assert family.people[0].role == "court clerk"
    assert family.people[0].role != "city judge"


def test_eligible_job_template_allows_qualified_city_judge():
    job = eligible_job_template_for(
        "government",
        0,
        age=45,
        education="graduate",
        experience_years=15,
    )

    assert job.role == "city judge"
    assert job.branch == "judicial"


def test_trade_school_jobs_include_hvac_and_roofing_paths():
    hvac = eligible_job_template_for(
        "private_service",
        3,
        age=26,
        education="trade",
        experience_years=3,
    )
    roofing = eligible_job_template_for(
        "private_service",
        4,
        age=26,
        education="trade",
        experience_years=3,
    )

    assert hvac.role == "HVAC technician"
    assert hvac.sector == "hvac_services"
    assert roofing.role == "roofer"
    assert roofing.sector == "roofing_services"


def test_trade_school_program_catalog_includes_core_choices():
    programs = [trade_school_program_for(index) for index in range(16)]

    assert [program.program for program in programs[:3]] == [
        "plumbing technology",
        "HVAC technology",
        "roofing",
    ]
    assert {program.program for program in programs} >= {
        "electrical technology",
        "carpentry",
        "masonry",
        "welding",
        "automotive service technology",
        "diesel technology",
        "heavy equipment maintenance",
        "appliance repair",
        "security system installation",
        "building inspection",
        "drywall installation",
        "flooring installation",
        "solar photovoltaic installation",
    }
    assert trade_school_program_for(1).typical_skills == (
        "heating systems",
        "air conditioning",
        "refrigeration",
    )


def test_generate_family_agents_creates_organizations_for_business_owners():
    family = generate_family_agents(
        "hispanic",
        household_index=0,
        adults=1,
        job_pools=("business_owner",),
        adult_education=("trade",),
        adult_experience_years=(8,),
    )

    assert family.people[0].employment_status == "business_owner"
    assert family.people[0].role == "landscaping business owner"
    assert len(family.organizations) == 1
    assert family.organizations[0].organization_type == "business"
    assert family.organizations[0].sector == "landscaping"
    assert family.organizations[0].owner_ids == ("juan-hernandez-1",)
    assert family.organizations[0].customer_types == (
        "residents",
        "businesses",
        "city_contracts",
    )
    assert "serves businesses" in family.organizations[0].notes


def test_business_owner_jobs_include_hvac_and_roofing_businesses():
    hvac_family = generate_family_agents(
        "anglo",
        household_index=3,
        adults=1,
        job_pools=("business_owner",),
        adult_education=("trade",),
        adult_experience_years=(8,),
    )
    roofing_family = generate_family_agents(
        "anglo",
        household_index=4,
        adults=1,
        job_pools=("business_owner",),
        adult_education=("trade",),
        adult_experience_years=(8,),
    )

    assert hvac_family.people[0].role == "HVAC business owner"
    assert hvac_family.organizations[0].sector == "hvac_services"
    assert roofing_family.people[0].role == "roofing business owner"
    assert roofing_family.organizations[0].sector == "roofing_services"


def test_generate_family_population_returns_businesses_after_people():
    population = generate_family_population(
        (
            FamilyGenerationSpec(
                "hispanic",
                household_index=0,
                adults=1,
                job_pools=("business_owner",),
                adult_education=("trade",),
                adult_experience_years=(8,),
            ),
        )
    )

    assert population.households[0].agent_id == "hernandez"
    assert population.people[0].household_id == "hernandez"
    assert population.organizations[0].sector == "landscaping"


def test_job_template_for_rejects_unknown_pool():
    try:
        job_template_for("moon_base", 0)
    except ValueError as exc:
        assert "unknown job pool" in str(exc)
    else:
        raise AssertionError("unknown job pool should be rejected")


def test_generate_family_agents_rejects_unknown_heritage():
    try:
        generate_family_agents("unknown")
    except ValueError as exc:
        assert "unknown heritage" in str(exc)
    else:
        raise AssertionError("unknown heritage should be rejected")


def test_generate_family_agents_rejects_invalid_family_sizes():
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


def test_generate_family_agents_rejects_child_parent():
    try:
        generate_family_agents("anglo", adults=1, adult_ages=(5,))
    except ValueError as exc:
        assert "at least 18 years old" in str(exc)
    else:
        raise AssertionError("child adult profile should be rejected")


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
