from math import isclose

from city_simulator import (
    Agent,
    CityState,
    Demographics,
    HouseholdAgent,
    InventoryState,
    InventoryStatusView,
    LanguageAccessView,
    LanguageProfile,
    LanguageSkill,
    OrganizationAgent,
    Parcel,
    ParcelDevelopmentView,
    ParcelOccupancy,
    PersonAgent,
    PopulationStructureView,
    ServiceLanguage,
    ZoningEnvelope,
    language_service_access_score,
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


def test_parcel_development_view_rolls_up_development_and_business_signals():
    state = CityState(
        parcels={
            "home": Parcel(
                "home",
                grid_x=1,
                grid_y=1,
                land_use="residential",
                development_stage="fully_developed",
                housing_units=30,
                max_housing_units=30,
                assessed_value=4_000_000,
                occupancy=ParcelOccupancy(household_ids=("household-1",)),
            ),
            "underused": Parcel(
                "underused",
                grid_x=3,
                grid_y=1,
                land_use="mixed_use",
                development_stage="underused",
                zoning=ZoningEnvelope(allowed_uses=("residential", "commercial", "mixed_use")),
                housing_units=4,
                max_housing_units=40,
                jobs=8,
                max_jobs=55,
                assessed_value=2_000_000,
                vacancy_rate=0.3,
                underused=True,
            ),
            "business": Parcel(
                "business",
                grid_x=5,
                grid_y=2,
                land_use="commercial",
                development_stage="fully_developed",
                zoning=ZoningEnvelope(allowed_uses=("commercial",)),
                jobs=80,
                max_jobs=120,
                assessed_value=8_000_000,
                occupancy=ParcelOccupancy(organization_ids=("org-1",)),
            ),
            "wetland": Parcel(
                "wetland",
                grid_x=4,
                grid_y=4,
                natural_cover="wetland",
                development_stage="pristine",
                zoning=ZoningEnvelope(allowed_uses=("residential",)),
                max_housing_units=20,
                assessed_value=500_000,
            ),
            "utility-gap": Parcel(
                "utility-gap",
                grid_x=9,
                grid_y=2,
                development_stage="vacant",
                max_housing_units=10,
                constraints=("utility_unready",),
            ),
            "outside-city": Parcel(
                "outside-city",
                grid_x=10,
                grid_y=10,
                reserved=True,
                reserved_for="neighbor-city",
                zoning=ZoningEnvelope(allowed_uses=("residential", "commercial")),
                max_housing_units=500,
                max_jobs=500,
                assessed_value=99_000_000,
            ),
        },
        households=(
            HouseholdAgent(
                "household-1",
                member_ids=("person-1",),
                income_band="middle",
                parcel_id="home",
            ),
        ),
        people=(
            PersonAgent(
                "person-1",
                household_id="household-1",
                age=34,
                income_band="middle",
                parcel_id="home",
            ),
        ),
        organizations=(
            OrganizationAgent("org-1", organization_type="business", parcel_id="business"),
        ),
    )

    view = ParcelDevelopmentView.derive(state)

    assert view.name == "parcel_development"
    assert view.source_dependencies == (
        "parcel_grid",
        "parcels",
        "households",
        "organizations",
    )
    assert view.parcel_count == 6
    assert view.reserved_parcels == 1
    assert view.buildable_housing_capacity == 46
    assert view.buildable_job_capacity == 87
    assert view.underused_parcels == 1
    assert view.redevelopment_candidate_parcels == 2
    assert view.vacant_or_undeveloped_parcels == 2
    assert view.utility_ready_parcels == 4
    assert view.environmentally_constrained_parcels == 1
    assert view.assessed_value == 14_500_000
    assert view.average_customer_access_steps == 5
    assert view.average_labor_access_steps == 5


def test_parcel_development_view_exports_plain_values():
    view = ParcelDevelopmentView.derive(CityState())

    assert set(view.as_dict()) == {
        "parcel_count",
        "reserved_parcels",
        "buildable_housing_capacity",
        "buildable_job_capacity",
        "underused_parcels",
        "redevelopment_candidate_parcels",
        "vacant_or_undeveloped_parcels",
        "utility_ready_parcels",
        "environmentally_constrained_parcels",
        "assessed_value",
        "average_customer_access_steps",
        "average_labor_access_steps",
    }


def test_inventory_status_view_derives_from_inventory_records():
    state = CityState(
        inventories=(
            InventoryState(
                holder_type="household",
                holder_id="household-1",
                sector="household",
                good="food",
                quantity=4,
                daily_use=2,
                reorder_threshold_days=3,
                reserve_target_days=5,
            ),
            InventoryState(
                holder_type="organization",
                holder_id="restaurant-1",
                sector="restaurant",
                good="fresh_food",
                days_on_hand=3,
                reorder_threshold_days=4,
                reserve_target_days=6,
                storage_type="refrigerated",
                spoilage_risk=0.5,
            ),
        )
    )

    view = InventoryStatusView.derive(state)

    assert view.name == "inventory_status"
    assert view.source_dependencies == ("inventories",)
    assert view.inventory_records == 2
    assert view.low_inventory_records == 2
    assert isclose(view.reserve_gap_days, 7.5)
    assert isclose(view.cold_chain_exposure_records, 1)


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


def test_population_structure_views_converge_for_matching_state_and_people():
    state = CityState(
        population=100,
        demographics=Demographics(
            children=20,
            working_age=50,
            seniors=30,
            low_income=20,
            middle_income=50,
            high_income=30,
        ),
    )
    people = (
        PersonAgent("child-1", "family-1", age=8, income_band="low", weight=20),
        PersonAgent("worker-1", "family-1", age=36, income_band="middle", weight=50),
        PersonAgent("senior-1", "family-2", age=72, income_band="high", weight=30),
    )

    aggregate_view = PopulationStructureView.derive(state)
    agent_view = PopulationStructureView.derive_from_people(people)

    assert aggregate_view.as_dict() == agent_view.as_dict()


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


def test_language_service_access_scores_direct_overlap():
    person = PersonAgent(
        "person-1",
        household_id="household-1",
        age=34,
        income_band="middle",
        language_profile=LanguageProfile(
            skills=(LanguageSkill("spanish", spoken_proficiency="native"),)
        ),
    )
    organization = OrganizationAgent(
        "org-1",
        organization_type="clinic",
        service_languages=(
            ServiceLanguage("spanish", service_proficiency="professional"),
        ),
    )

    assert language_service_access_score(person, organization) == 75


def test_language_service_access_uses_interpreter_capacity_as_bridge():
    person = PersonAgent(
        "person-1",
        household_id="household-1",
        age=34,
        income_band="middle",
        language_profile=LanguageProfile(
            skills=(LanguageSkill("english", spoken_proficiency="basic"),),
            interpreter_needed=True,
        ),
    )
    without_interpreter = OrganizationAgent(
        "org-1",
        organization_type="public_agency",
        service_languages=(
            ServiceLanguage("english", service_proficiency="professional"),
        ),
    )
    with_interpreter = OrganizationAgent(
        "org-2",
        organization_type="public_agency",
        service_languages=(
            ServiceLanguage(
                "english",
                service_proficiency="professional",
                interpreter_capacity=2,
            ),
        ),
    )

    assert language_service_access_score(person, without_interpreter) == 25
    assert language_service_access_score(person, with_interpreter) == 70


def test_language_service_access_scores_no_overlap_low():
    person = PersonAgent(
        "person-1",
        household_id="household-1",
        age=34,
        income_band="middle",
        language_profile=LanguageProfile(
            skills=(LanguageSkill("amharic", spoken_proficiency="native"),)
        ),
    )
    organization = OrganizationAgent(
        "org-1",
        organization_type="bank",
        service_languages=(
            ServiceLanguage("english", service_proficiency="professional"),
        ),
    )

    assert language_service_access_score(person, organization) == 0


def test_language_access_view_rolls_up_people_and_service_languages():
    state = CityState(
        people=(
            PersonAgent(
                "person-1",
                household_id="household-1",
                age=34,
                income_band="middle",
                weight=10,
                language_profile=LanguageProfile(
                    skills=(
                        LanguageSkill("english", spoken_proficiency="professional"),
                        LanguageSkill("spanish", spoken_proficiency="professional"),
                    )
                ),
            ),
            PersonAgent(
                "person-2",
                household_id="household-2",
                age=42,
                income_band="low",
                weight=30,
                language_profile=LanguageProfile(
                    skills=(LanguageSkill("amharic", spoken_proficiency="native"),),
                    interpreter_needed=True,
                ),
            ),
        ),
        organizations=(
            OrganizationAgent(
                "org-1",
                organization_type="clinic",
                service_languages=(
                    ServiceLanguage("english", service_proficiency="professional"),
                    ServiceLanguage("spanish", service_proficiency="professional"),
                ),
            ),
            OrganizationAgent(
                "org-2",
                organization_type="market",
            ),
        ),
    )

    view = LanguageAccessView.derive(state)

    assert view.name == "language_access"
    assert view.source_dependencies == ("people", "organizations")
    assert view.total_people_weight == 40
    assert view.organizations_with_service_languages == 1
    assert isclose(view.average_service_access_score, 18.75)
    assert isclose(view.limited_access_share, 0.75)
    assert isclose(view.interpreter_need_share, 0.75)
    assert isclose(view.multilingual_bridge_share, 0.25)
    assert set(view.as_dict()) == {
        "total_people_weight",
        "organizations_with_service_languages",
        "average_service_access_score",
        "limited_access_share",
        "interpreter_need_share",
        "multilingual_bridge_share",
    }
