from city_simulator import (
    CulturalAffiliation,
    CulturalIdentity,
    HouseholdAgent,
    LanguageProfile,
    LanguageSkill,
    PersonAgent,
    living_conditions_for,
)


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


def test_cultural_identity_derives_affiliations_from_legacy_cultures():
    identity = CulturalIdentity(cultures=("american", "israeli"))

    assert identity.cultures == ("american", "israeli")
    assert tuple(affiliation.culture for affiliation in identity.affiliations) == (
        "american",
        "israeli",
    )
    assert identity.strength_for("american") == 1.0
    israeli = identity.affiliation_for("israeli")
    assert israeli is not None
    assert israeli.source == "legacy_culture"


def test_cultural_identity_preserves_explicit_affiliation_strengths():
    identity = CulturalIdentity(
        cultures=("american", "israeli"),
        affiliations=(
            CulturalAffiliation("american", strength=1.0, source="self"),
            CulturalAffiliation(
                "israeli",
                strength=0.65,
                source="family",
                home_use=True,
                community_use=True,
                years_affiliated=12,
                tags=("diaspora",),
            ),
        ),
    )

    assert identity.strength_for("american") == 1.0
    assert identity.strength_for("israeli") == 0.65
    assert identity.strength_for("canadian") == 0.0
    israeli = identity.affiliation_for("israeli")
    assert israeli is not None
    assert israeli.tags == ("diaspora",)


def test_person_derives_native_language_profile_from_legacy_identity_languages():
    person = PersonAgent(
        "person-1",
        household_id="household-1",
        age=42,
        income_band="middle",
        identity=CulturalIdentity(languages=("english", "spanish")),
    )

    assert person.identity.languages == ("english", "spanish")
    assert person.language_profile.languages == ("english", "spanish")
    assert person.language_profile.preferred_language == "english"
    assert person.language_profile.household_languages == ("english", "spanish")
    assert person.language_profile.spoken_rank("spanish") == 4
    spanish = person.language_profile.skill_for("spanish")
    assert spanish is not None
    assert spanish.home_use


def test_explicit_language_profile_preserves_skill_specific_proficiency():
    profile = LanguageProfile(
        skills=(
            LanguageSkill(
                language="english",
                spoken_proficiency="basic",
                reading_proficiency="conversational",
                writing_proficiency="basic",
                needs_interpreter=True,
                years_learning=1.5,
                arrival_proficiency="none",
                learning_contexts=("work", "english_class"),
                exposure_score=32,
            ),
            LanguageSkill(language="amharic", spoken_proficiency="native", home_use=True),
        ),
        household_languages=("amharic",),
        preferred_language="amharic",
        interpreter_needed=True,
    )
    person = PersonAgent(
        "person-1",
        household_id="household-1",
        age=30,
        income_band="low",
        identity=CulturalIdentity(languages=("amharic",)),
        language_profile=profile,
    )

    assert person.language_profile.preferred_language == "amharic"
    assert person.language_profile.spoken_rank("english") == 1
    english = person.language_profile.skill_for("english")
    assert english is not None
    assert english.needs_interpreter
    assert english.learning_contexts == (
        "work",
        "english_class",
    )
    assert (
        person.language_profile.shared_spoken_rank(
            LanguageProfile(skills=(LanguageSkill("english", "professional"),))
        )
        == 1
    )
