from city_simulator import (
    COARSE_US_SYNTHETIC_PROFILE,
    FamilyGenerationSpec,
    JobTemplate,
    SyntheticPopulationRecipe,
    SyntheticPopulationSourceProfile,
    college_program_for,
    college_program_weight,
    college_programs_for_credential,
    eligible_job_template_for,
    generate_family_agents,
    generate_family_population,
    generate_synthetic_population,
    job_template_for,
    trade_school_program_for,
    weighted_college_program_for,
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

    assert family.household.agent_id == "household-0001-hernandez"
    assert family.household.member_ids == (
        "person-0001-01-juan-hernandez",
        "person-0001-02-louise-hernandez",
        "person-0001-03-renee-hernandez",
        "person-0001-04-jose-hernandez",
    )
    assert [person.display_name for person in family.people] == [
        "Juan Hernandez",
        "Louise Hernandez",
        "Renee Hernandez",
        "Jose Hernandez",
    ]
    assert all(person.household_id == "household-0001-hernandez" for person in family.people)
    assert all(person.neighborhood == "summer_crescent_boulevard" for person in family.people)
    assert family.support_need == 4
    assert family.support_capacity == 6
    assert family.support_gap == 0
    assert family.household.notes == ()


def test_generate_family_agents_is_deterministic_by_heritage_and_index():
    first = generate_family_agents("jewish", household_index=2, adults=1, children=1)
    second = generate_family_agents("jewish", household_index=2, adults=1, children=1)

    assert first == second
    assert first.household.agent_id == "household-0003-levine"
    assert first.people[0].display_name == "Ari Levine"


def test_generate_family_agents_supports_dmv_heritage_name_banks():
    expected_cultures = {
        "chinese": "chinese",
        "japanese": "japanese",
        "thai": "thai",
        "korean": "korean",
        "russian": "russian",
        "ukrainian": "ukrainian",
        "ethiopian": "ethiopian",
        "egyptian": "egyptian",
        "israeli": "israeli",
        "israeli arab": "israeli_arab",
        "french": "french",
        "spanish": "spanish",
        "latino": "latino",
        "mexican": "mexican",
        "guatemalan": "guatemalan",
        "brazilian": "brazilian",
        "portuguese": "portuguese",
        "canadian": "canadian",
        "american": "american",
        "romanian": "romanian",
        "polish": "polish",
        "bulgarian": "bulgarian",
        "black american": "black_american",
        "nigerian": "nigerian",
        "cameroon": "cameroonian",
        "haitian": "haitian",
        "vietnamese": "vietnamese",
    }

    for heritage, expected_culture in expected_cultures.items():
        family = generate_family_agents(heritage, household_index=0, adults=1, children=1)

        assert family.household.agent_id
        assert len(family.people) == 2
        assert family.people[0].identity.cultures == (expected_culture,)
        assert family.people[0].identity.affiliations[0].culture == expected_culture
        assert family.people[0].identity.affiliations[0].strength == 1.0
        assert family.people[0].identity.languages
        assert family.people[1].identity.cultures == (expected_culture,)
        assert family.people[1].identity.strength_for(expected_culture) == 1.0


def test_generate_family_agents_accepts_common_heritage_aliases():
    israeli_arab = generate_family_agents("israeli arab", adults=1)
    misspelled_guatemalan = generate_family_agents("guatamalan", adults=1)
    misspelled_cameroonian = generate_family_agents("camaroon", adults=1)

    assert israeli_arab.people[0].identity.cultures == ("israeli_arab",)
    assert misspelled_guatemalan.people[0].identity.cultures == ("guatemalan",)
    assert misspelled_cameroonian.people[0].identity.cultures == ("cameroonian",)


def test_generated_family_derives_language_profile_from_heritage_languages():
    family = generate_family_agents("haitian", adults=1)

    assert family.people[0].identity.languages == ("haitian_creole", "french")
    assert not hasattr(family.people[0].identity, "language_proficiency")
    assert family.people[0].language_profile.languages == ("haitian_creole", "french")
    assert family.people[0].language_profile.preferred_language == "haitian_creole"
    haitian_creole = family.people[0].language_profile.skill_for("haitian_creole")
    assert haitian_creole is not None
    assert haitian_creole.spoken_proficiency == "native"


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
    assert child.identity.strength_for("anglo") == 1.0
    assert child.adoption.is_adopted
    assert child.adoption.birth_parent_ethnicities == ("hispanic", "jewish")
    assert child.adoption.birth_parent_cultures == ("hispanic", "jewish")
    assert child.adoption.adoptive_parent_ethnicities == ("anglo",)
    assert child.adoption.raised_cultures == ("anglo",)
    assert child.parent_ids == (
        "person-0001-01-dorothy-jones",
        "person-0001-02-ron-jones",
    )


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
        "household-0001-hernandez",
        "household-0002-harcourt",
    ]
    assert [household.agent_id for household in population.households] == [
        "household-0001-hernandez",
        "household-0002-harcourt",
    ]
    assert [person.household_id for person in population.people] == [
        "household-0001-hernandez",
        "household-0001-hernandez",
        "household-0001-hernandez",
        "household-0001-hernandez",
        "household-0002-harcourt",
        "household-0002-harcourt",
    ]
    assert population.organizations == ()


def test_generate_synthetic_population_creates_exact_count():
    population = generate_synthetic_population(5)

    assert len(population.people) == 5
    assert len(population.households) >= 1
    assert population.people == tuple(
        person for family in population.families for person in family.people
    )
    assert all(person.household_id for person in population.people)
    assert all(person.identity.cultures for person in population.people)
    assert any(person.role for person in population.people if not person.is_child)


def test_generate_synthetic_population_derives_adult_income_from_jobs():
    population = generate_synthetic_population(5)

    assert [person.income_band for person in population.people] == [
        "low",
        "low",
        "middle",
        "middle",
        "middle",
    ]


def test_generate_synthetic_population_is_deterministic():
    first = generate_synthetic_population(7)
    second = generate_synthetic_population(7)

    assert first == second


def test_generate_synthetic_population_uses_recipe_weights():
    recipe = SyntheticPopulationRecipe(
        heritages=(("jewish", 1.0),),
        household_shapes=((1, 0, 1.0),),
        income_bands=(("high", 1.0),),
        neighborhoods=(("market_district", "high", 1.0),),
        job_pools=(("government", 1.0),),
    )

    population = generate_synthetic_population(3, recipe)

    assert len(population.people) == 3
    assert {person.identity.cultures for person in population.people} == {("jewish",)}
    assert {person.neighborhood for person in population.people} == {"market_district"}
    assert {person.income_band for person in population.people} == {"middle"}
    assert [person.role for person in population.people] == [
        "court clerk",
        "court clerk",
        "legislative aide",
    ]


def test_generate_synthetic_population_adds_cultural_religious_institutions():
    recipe = SyntheticPopulationRecipe(
        heritages=(("jewish", 1.0),),
        household_shapes=((1, 0, 1.0),),
        income_bands=(("middle", 1.0),),
        neighborhoods=(("summer_crescent_boulevard", "middle", 1.0),),
        job_pools=(("private_service", 1.0),),
    )

    population = generate_synthetic_population(3, recipe)

    assert [organization.display_name for organization in population.organizations] == [
        "Jewish synagogue",
    ]
    assert population.organizations[0].notes == (
        "serves jewish community",
        "leader role: rabbi",
    )


def test_generate_synthetic_population_adds_hispanic_church_and_bishop_context():
    recipe = SyntheticPopulationRecipe(
        heritages=(("hispanic", 1.0),),
        household_shapes=((1, 0, 1.0),),
        income_bands=(("middle", 1.0),),
        neighborhoods=(("summer_crescent_boulevard", "middle", 1.0),),
        job_pools=(("private_service", 1.0),),
    )

    population = generate_synthetic_population(15, recipe)

    assert [organization.display_name for organization in population.organizations] == [
        "Hispanic church",
        "Hispanic diocese office",
    ]
    assert population.organizations[0].notes[1] == "leader role: priest"
    assert population.organizations[1].notes[1] == "leader role: bishop"


def test_faith_leaders_are_job_templates_with_prerequisites():
    young_worker = eligible_job_template_for(
        "faith_leader",
        0,
        age=30,
        education="graduate",
        experience_years=4,
    )
    senior_worker = eligible_job_template_for(
        "faith_leader",
        3,
        age=52,
        education="graduate",
        experience_years=20,
    )

    assert young_worker.role == "rabbi"
    assert young_worker.required_education == "graduate"
    assert senior_worker.role == "bishop"
    assert senior_worker.min_experience_years == 15


def test_coarse_synthetic_profile_documents_source_assumptions():
    assert COARSE_US_SYNTHETIC_PROFILE.name == "coarse_us_proxy"
    assert any("ACS/PUMS" in note for note in COARSE_US_SYNTHETIC_PROFILE.source_notes)
    assert any("IPEDS" in note for note in COARSE_US_SYNTHETIC_PROFILE.source_notes)
    assert any("BLS" in note for note in COARSE_US_SYNTHETIC_PROFILE.source_notes)


def test_synthetic_source_profile_converts_to_recipe():
    profile = SyntheticPopulationSourceProfile(
        name="test_profile",
        heritages=(("hispanic", 1.0),),
        household_shapes=((2, 1, 1.0),),
        income_bands=(("middle", 1.0),),
        neighborhoods=(("summer_crescent_boulevard", "middle", 1.0),),
        job_pools=(("private_service", 1.0),),
        source_notes=("fixture profile",),
    )

    population = generate_synthetic_population(3, profile.as_recipe())

    assert len(population.people) == 3
    assert len(population.households) == 1
    assert {person.identity.cultures for person in population.people} == {("hispanic",)}
    assert {person.neighborhood for person in population.people} == {
        "summer_crescent_boulevard",
    }


def test_generate_synthetic_population_rejects_negative_count():
    try:
        generate_synthetic_population(-1)
    except ValueError as exc:
        assert "count must be non-negative" in str(exc)
    else:
        raise AssertionError("negative synthetic population count should be rejected")


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


def test_trade_income_progresses_with_experience():
    plumber = JobTemplate(
        role="plumber",
        employment_status="employed",
        income_band="middle",
        employer_type="private_business",
        sector="plumbing_services",
        required_education="trade",
        min_experience_years=1,
        entry_income_band="middle",
        experienced_income_band="high",
    )
    entry = generate_family_agents(
        "anglo",
        adults=1,
        adult_jobs=(plumber,),
        adult_ages=(26,),
        adult_education=("trade",),
        adult_experience_years=(2,),
    )
    experienced = generate_family_agents(
        "anglo",
        adults=1,
        adult_jobs=(plumber,),
        adult_ages=(42,),
        adult_education=("trade",),
        adult_experience_years=(18,),
    )

    assert entry.people[0].role == "plumber"
    assert entry.people[0].income_band == "middle"
    assert experienced.people[0].role == "plumber"
    assert experienced.people[0].income_band == "high"


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


def test_college_program_catalog_includes_cip_backed_disciplines():
    programs = [college_program_for(index) for index in range(10)]

    assert [program.major for program in programs[:5]] == [
        "business administration",
        "accounting",
        "finance",
        "public administration",
        "law",
    ]
    assert {program.discipline for program in programs} >= {
        "business",
        "public affairs",
        "legal studies",
        "public safety",
        "education",
        "health professions",
        "computer and information sciences",
    }


def test_college_programs_can_be_filtered_by_credential_level():
    masters_programs = college_programs_for_credential("masters")
    doctorate_programs = college_programs_for_credential("doctorate")

    assert "business administration" in {program.major for program in masters_programs}
    assert "nursing" in {program.major for program in masters_programs}
    assert "law" not in {program.major for program in masters_programs}
    assert "computer science" in {program.major for program in doctorate_programs}


def test_college_program_weights_make_major_selection_non_uniform():
    business = college_program_for(0)
    history = next(
        program for program in college_programs_for_credential("bachelors")
        if program.major == "history"
    )

    assert college_program_weight(business, "bachelors") > college_program_weight(
        history,
        "bachelors",
    )
    assert weighted_college_program_for("bachelors", 0).discipline == "business"
    assert weighted_college_program_for("masters", 0).discipline == "business"
    assert weighted_college_program_for("doctorate", 0).discipline == "health professions"


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
    assert family.organizations[0].owner_ids == ("person-0001-01-juan-hernandez",)
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

    assert population.households[0].agent_id == "household-0001-hernandez"
    assert population.people[0].household_id == "household-0001-hernandez"
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
