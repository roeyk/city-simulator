import pytest

from city_simulator import living_conditions_for
from city_simulator.scenario import (
    ScenarioError,
    city_from_mapping,
    load_city,
    load_scenario,
    save_city,
)


def test_city_from_mapping_keeps_defaults_for_missing_fields():
    city = city_from_mapping({"population": 50_000, "demographics": {"children": 9_000}})

    assert city.population == 50_000
    assert city.demographics.children == 9_000
    assert city.demographics.working_age == 62_000


def test_ten_citizen_mvp_city_loads():
    city = load_city("examples/cities/ten-citizen-mvp.json")

    assert city.population == 10
    assert len(city.people) == 10
    assert len(city.households) == 5
    assert len(city.organizations) >= 20
    assert city.budget == 0
    assert city.annual_income == 45_000_000
    assert city.annual_budget == 50_000_000
    assert city.revenue_sources.total == 45_000_000
    assert city.revenue_sources.business_taxes == 6_000_000
    assert city.revenue_sources.state_grants == 12_000_000
    assert city.pollution == 22
    assert city.neighborhoods["village_hills"].housing_units == 160
    assert city.neighborhoods["summer_crescent_boulevard"].housing_units == 30
    assert city.place_assets[0].name == "Woodlawn Elementary School"
    assert city.place_assets[1].name == "Northbridge Middle and High School"
    assert city.people[0].display_name == "Juan Hernandez"
    assert "mortgage 25% paid" in city.households[0].debts
    hernandez = next(household for household in city.households if household.agent_id == "hernandez")
    renee = next(person for person in city.people if person.agent_id == "renee-hernandez")
    assert renee.housing_status == ""
    assert living_conditions_for(renee, hernandez).housing_status == "single-family house"
    assert city.pending_effects[0].target == "civic_trust"
    assert city.pending_effects[0].tags == (
        "corruption",
        "contractors",
        "government_sector",
    )


def test_city_from_mapping_reads_sensitivity():
    city = city_from_mapping(
        {
            "population": 50_000,
            "sensitivity": {
                "crime_unemployment": 1.4,
                "sentiment_financial_stress": 0.8,
            },
        }
    )

    assert city.sensitivity.crime_unemployment == 1.4
    assert city.sensitivity.sentiment_financial_stress == 0.8


def test_city_from_mapping_reads_housing_stock_and_assistance():
    city = city_from_mapping(
        {
            "housing_stock": {
                "estate_home_units": 20,
                "mixed_use_shopfront_units": 75,
                "garden_apartment_units": 300,
                "built_1940_1979_units": 220,
            },
            "housing_assistance": {
                "section8_vouchers": 100,
                "voucher_utilization_rate": 0.8,
                "landlord_acceptance_rate": 0.5,
                "inspection_pass_rate": 0.9,
                "shelter_beds": 40,
                "transitional_housing_units": 15,
                "permanent_supportive_housing_units": 25,
            },
        }
    )

    assert city.housing_stock.total_units == 395
    assert city.housing_stock.built_1940_1979_units == 220
    assert city.housing_assistance.usable_vouchers == pytest.approx(36)
    assert city.housing_assistance.emergency_shelter_capacity == 55
    assert city.housing_assistance.long_term_housing_stability_capacity == pytest.approx(61)


def test_city_from_mapping_reads_neighborhood_microcosms():
    city = city_from_mapping(
        {
            "neighborhoods": {
                "market-district": {
                    "area_square_miles": 1.2,
                    "population": 8000,
                    "housing_units": 4200,
                    "jobs": 7000,
                    "land_use_mix": {"residential": 45, "retail": 35, "office": 20},
                    "adjacent_neighborhoods": ["old-town"],
                    "adjacent_sectors": ["retail_corridor", "transit_hub"],
                    "housing_stock": {
                        "mixed_use_shopfront_units": 900,
                        "highrise_apartment_units": 1200,
                    },
                    "housing_assistance": {
                        "section8_vouchers": 150,
                        "voucher_utilization_rate": 0.7,
                        "landlord_acceptance_rate": 0.6,
                        "inspection_pass_rate": 0.8,
                    },
                }
            }
        }
    )

    neighborhood = city.neighborhoods["market-district"]
    assert neighborhood.name == "market-district"
    assert neighborhood.adjacent_neighborhoods == ("old-town",)
    assert neighborhood.adjacent_sectors == ("retail_corridor", "transit_hub")
    assert neighborhood.housing_stock.total_units == 2100
    assert neighborhood.housing_assistance.usable_vouchers == pytest.approx(50.4)


def test_city_from_mapping_reads_neighborhood_zoning_envelopes():
    city = city_from_mapping(
        {
            "neighborhoods": {
                "station-quarter": {
                    "zoning": {
                        "allowed_uses": [
                            "residential",
                            "commercial",
                            "mixed_use",
                            "civic",
                        ],
                        "overlay_tags": [
                            "inclusionary_zoning",
                            "transit_oriented_development",
                            "redevelopment_district",
                        ],
                        "special_permit_uses": ["institutional", "special_purpose"],
                        "max_housing_units": 6200,
                        "max_commercial_jobs": 2400,
                        "max_industrial_jobs": 120,
                        "max_civic_capacity": 900,
                        "max_density_per_square_mile": 18000,
                        "max_floor_area_ratio": 4.5,
                        "max_height_stories": 12,
                        "max_lot_coverage": 0.82,
                        "parking_spaces_per_home": 0.4,
                        "inclusionary_housing_share": 0.18,
                        "affordable_housing_bonus": 0.25,
                        "historic_preservation_score": 0.15,
                        "environmental_constraint_score": 0.2,
                        "transit_oriented_development_score": 0.85,
                        "redevelopment_priority": 0.7,
                        "industrial_protection_score": 0.1,
                    }
                }
            }
        }
    )

    zoning = city.neighborhoods["station-quarter"].zoning
    assert zoning.allowed_uses == ("residential", "commercial", "mixed_use", "civic")
    assert zoning.overlay_tags == (
        "inclusionary_zoning",
        "transit_oriented_development",
        "redevelopment_district",
    )
    assert zoning.special_permit_uses == ("institutional", "special_purpose")
    assert zoning.max_housing_units == 6200
    assert zoning.max_commercial_jobs == 2400
    assert zoning.max_floor_area_ratio == pytest.approx(4.5)
    assert zoning.parking_spaces_per_home == pytest.approx(0.4)
    assert zoning.inclusionary_housing_share == pytest.approx(0.18)
    assert zoning.transit_oriented_development_score == pytest.approx(0.85)


def test_city_from_mapping_rejects_invalid_neighborhood_zoning_shape():
    with pytest.raises(ScenarioError, match="neighborhood central zoning must be an object"):
        city_from_mapping({"neighborhoods": {"central": {"zoning": ["residential"]}}})


def test_city_from_mapping_rejects_invalid_neighborhood_zoning_arrays():
    with pytest.raises(ScenarioError, match="allowed_uses must be an array"):
        city_from_mapping(
            {
                "neighborhoods": {
                    "central": {
                        "zoning": {
                            "allowed_uses": "residential",
                        }
                    }
                }
            }
        )


def test_city_from_mapping_reads_place_assets_and_embedded_services():
    city = city_from_mapping(
        {
            "place_assets": [
                {
                    "name": "City General Hospital",
                    "asset_type": "hospital",
                    "capacity": 600,
                    "jobs": 2200,
                    "condition": 82,
                    "access_score": 71,
                    "service_area": ["north", "central"],
                    "tags": ["regional_anchor"],
                    "schedule": {
                        "schedule_type": "24x7",
                        "days": ["weekday", "weekend"],
                        "peak_periods": ["overnight", "flu_season"],
                        "annual_hours": 8760,
                        "daytime_share": 0.34,
                        "evening_share": 0.33,
                        "overnight_share": 0.33,
                    },
                    "services": [
                        {
                            "name": "Emergency Department",
                            "service_type": "emergency_care",
                            "capacity": 160,
                            "quality": 78,
                            "access": 74,
                            "trust": 69,
                            "staff": 90,
                            "target_groups": ["all_residents"],
                            "schedule": {
                                "schedule_type": "24x7",
                                "annual_hours": 8760,
                                "overnight_share": 0.33,
                            },
                        },
                        {
                            "name": "Outpatient Therapy",
                            "service_type": "mental_health",
                            "capacity": 45,
                            "quality": 72,
                        },
                    ],
                }
            ],
            "neighborhoods": {
                "market-district": {
                    "place_assets": [
                        {
                            "name": "Market Arcade",
                            "asset_type": "mixed_use",
                            "capacity": 900,
                            "jobs": 350,
                            "schedule": {
                                "schedule_type": "business_hours",
                                "days": ["weekday", "weekend"],
                                "daytime_share": 0.75,
                                "evening_share": 0.25,
                            },
                            "services": [
                                {
                                    "name": "Ground Floor Retail",
                                    "service_type": "retail",
                                    "capacity": 550,
                                }
                            ],
                        }
                    ]
                }
            },
        }
    )

    hospital = city.place_assets[0]
    market_arcade = city.neighborhoods["market-district"].place_assets[0]

    assert hospital.service_area == ("north", "central")
    assert hospital.tags == ("regional_anchor",)
    assert hospital.schedule.schedule_type == "24x7"
    assert hospital.schedule.days == ("weekday", "weekend")
    assert hospital.schedule.peak_periods == ("overnight", "flu_season")
    assert hospital.services[0].schedule.is_overnight_oriented
    assert hospital.services[0].target_groups == ("all_residents",)
    assert hospital.service_capacity() == 205
    assert hospital.service_capacity("mental_health") == 45
    assert market_arcade.neighborhood == "market-district"
    assert market_arcade.schedule.is_daytime_oriented
    assert city.neighborhoods["market-district"].service_capacity("retail") == 550
    assert city.service_capacity("retail") == 550
    assert city.service_capacity("emergency_care") == 160
    assert city.service_capacity() == 755


def test_city_from_mapping_reads_daytime_school_and_night_street_cleaning_schedules():
    city = city_from_mapping(
        {
            "place_assets": [
                {
                    "name": "Public Works Depot",
                    "asset_type": "public_works_depot",
                    "services": [
                        {
                            "name": "Street Cleaning",
                            "service_type": "street_cleaning",
                            "capacity": 42,
                            "schedule": {
                                "schedule_type": "overnight",
                                "days": ["weekday"],
                                "peak_periods": ["overnight"],
                                "start_hour": 22,
                                "end_hour": 5,
                                "overnight_share": 0.85,
                                "noise_burden": 0.2,
                                "disruption_burden": 0.1,
                            },
                        }
                    ],
                }
            ],
            "neighborhoods": {
                "central": {
                    "place_assets": [
                        {
                            "name": "Central Elementary",
                            "asset_type": "school",
                            "services": [
                                {
                                    "name": "K-5 Seats",
                                    "service_type": "education",
                                    "capacity": 520,
                                    "schedule": {
                                        "schedule_type": "daytime_school",
                                        "days": ["weekday"],
                                        "seasons": ["school_year"],
                                        "peak_periods": ["morning", "afternoon"],
                                        "start_hour": 8,
                                        "end_hour": 15,
                                        "daytime_share": 0.95,
                                    },
                                }
                            ],
                        }
                    ]
                }
            },
        }
    )

    street_cleaning = city.place_assets[0].services[0]
    school_service = city.neighborhoods["central"].place_assets[0].services[0]

    assert street_cleaning.schedule.is_overnight_oriented
    assert street_cleaning.schedule.days == ("weekday",)
    assert street_cleaning.schedule.noise_burden == pytest.approx(0.2)
    assert school_service.schedule.is_daytime_oriented
    assert school_service.schedule.seasons == ("school_year",)


def test_city_from_mapping_reads_financial_institution_profiles():
    city = city_from_mapping(
        {
            "place_assets": [
                {
                    "name": "Main Street Federal Credit Union",
                    "asset_type": "federal_credit_union",
                    "financial_profile": {
                        "institution_type": "credit_union",
                        "charter": "federal",
                        "market_roles": ["deposits", "consumer_lending", "mortgages"],
                        "asset_classes": ["cash", "consumer_credit", "mortgages"],
                        "deposit_capacity": 250000000,
                        "lending_capacity": 140000000,
                        "household_access_score": 82,
                        "business_access_score": 54,
                        "liquidity_score": 76,
                        "risk_score": 28,
                    },
                    "services": [
                        {
                            "name": "Member Lending",
                            "service_type": "household_credit",
                            "capacity": 1800,
                        }
                    ],
                },
                {
                    "name": "Regional Market Access Office",
                    "asset_type": "market_exchange_access",
                    "financial_profile": {
                        "institution_type": "exchange_market_access",
                        "market_roles": [
                            "energy_exchange",
                            "stock_market",
                            "bond_market",
                            "commodities_market",
                        ],
                        "participant_roles": [
                            "energy_supplier",
                            "county_distributor",
                            "large_energy_consumer",
                            "speculator",
                        ],
                        "asset_classes": [
                            "power",
                            "natural_gas",
                            "environmental_products",
                            "equities",
                            "municipal_bonds",
                            "commodities",
                        ],
                        "municipal_finance_capacity": 500000000,
                        "business_access_score": 78,
                        "liquidity_score": 83,
                        "risk_score": 62,
                    },
                    "services": [
                        {
                            "name": "Municipal Bond Desk",
                            "service_type": "municipal_finance",
                            "capacity": 12,
                        },
                        {
                            "name": "Energy Hedging Access",
                            "service_type": "energy_market_access",
                            "capacity": 8,
                        },
                    ],
                },
            ]
        }
    )

    credit_union = city.place_assets[0].financial_profile
    market_access = city.place_assets[1].financial_profile

    assert credit_union is not None
    assert credit_union.charter == "federal"
    assert credit_union.market_roles == ("deposits", "consumer_lending", "mortgages")
    assert credit_union.deposit_capacity == pytest.approx(250_000_000)
    assert market_access is not None
    assert "energy_exchange" in market_access.market_roles
    assert market_access.participant_roles == (
        "energy_supplier",
        "county_distributor",
        "large_energy_consumer",
        "speculator",
    )
    assert "natural_gas" in market_access.asset_classes
    assert "environmental_products" in market_access.asset_classes
    assert "municipal_bonds" in market_access.asset_classes
    assert city.service_capacity("municipal_finance") == 12
    assert city.service_capacity("energy_market_access") == 8


def test_city_from_mapping_reads_pending_effects():
    city = city_from_mapping(
        {
            "pending_effects": [
                {
                    "source": "summer_blackout",
                    "target": "civic_trust",
                    "amount": -4.0,
                    "delay_turns": 0,
                    "duration_turns": 3,
                    "decay_rate": 0.25,
                    "tags": ["heat", "grid", "public_trust"],
                    "explanation": "Blackouts damaged confidence in emergency planning.",
                }
            ]
        }
    )

    effect = city.pending_effects[0]

    assert effect.source == "summer_blackout"
    assert effect.target == "civic_trust"
    assert effect.amount == pytest.approx(-4.0)
    assert effect.is_active
    assert effect.tags == ("heat", "grid", "public_trust")


def test_load_scenario_reads_name_policy_and_years(tmp_path):
    path = tmp_path / "housing.json"
    path.write_text(
        """
        {
          "name": "housing first",
          "years": 12,
          "policy": {
            "tax_rate": 0.2,
            "housing_investment": 70000000
          }
        }
        """,
        encoding="utf-8",
    )

    name, policy, external, years = load_scenario(path)

    assert name == "housing first"
    assert policy.tax_rate == 0.2
    assert policy.housing_investment == 70_000_000
    assert external.county_funding == 0
    assert years == 12


def test_prosock_business_tax_increase_scenario_loads():
    name, policy, _external, years = load_scenario(
        "examples/scenarios/prosock-business-tax-increase.json"
    )

    assert name == "Prosock business tax increase"
    assert policy.business_tax_rate == 0.15
    assert years == 1


def test_load_scenario_reads_higher_level_controls(tmp_path):
    path = tmp_path / "controlled.json"
    path.write_text(
        """
        {
          "name": "county-state-country controls",
          "policy": {
            "citizen_influx_rate": 0.01,
            "zoning_restrictiveness": 0.2
          },
          "county": {
            "funding": 10000000,
            "housing_directive": 25000000
          },
          "state": {
            "environment_mandate": 30000000
          },
          "country": {
            "funding": 15000000,
            "growth_pressure": 0.003,
            "interest_rate": 0.035
          }
        }
        """,
        encoding="utf-8",
    )

    _, policy, external, _ = load_scenario(path)

    assert policy.citizen_influx_rate == 0.01
    assert policy.zoning_restrictiveness == 0.2
    assert external.county_funding == 10_000_000
    assert external.county_housing_directive == 25_000_000
    assert external.state_environment_mandate == 30_000_000
    assert external.federal_funding == 15_000_000
    assert external.federal_growth_pressure == 0.003
    assert external.national_interest_rate == 0.035


def test_load_scenario_rejects_unknown_fields(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"policy": {"parks": 10}}', encoding="utf-8")

    with pytest.raises(ScenarioError, match="unknown policy fields"):
        load_scenario(path)


def test_save_city_round_trips_named_city(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    city = city_from_mapping(
        {
            "population": 1234,
            "year": 2,
            "sensitivity": {"crime_unemployment": 1.25},
            "housing_assistance": {"shelter_beds": 12},
            "people": [
                {
                    "agent_id": "person-1",
                    "household_id": "household-1",
                    "age": 35,
                    "income_band": "middle",
                    "weight": 20,
                    "parent_ids": ["birth-parent-1", "birth-parent-2"],
                    "identity": {
                        "ethnicities": ["hispanic", "jewish"],
                        "cultures": ["anglo"],
                        "languages": ["english", "spanish"],
                        "religion": "jewish",
                        "religiosity": "medium",
                        "affiliations": [
                            {
                                "culture": "anglo",
                                "strength": 0.7,
                                "source": "raised_culture",
                                "home_use": True,
                                "community_use": True,
                                "self_identified": True,
                                "years_affiliated": 30,
                                "tags": ["household"],
                            },
                            {
                                "culture": "hispanic",
                                "strength": 0.45,
                                "source": "family",
                                "self_identified": True,
                            },
                        ],
                    },
                    "language_profile": {
                        "preferred_language": "spanish",
                        "household_languages": ["spanish"],
                        "interpreter_needed": True,
                        "skills": [
                            {
                                "language": "english",
                                "spoken_proficiency": "basic",
                                "reading_proficiency": "conversational",
                                "writing_proficiency": "basic",
                                "needs_interpreter": True,
                                "years_learning": 2,
                                "arrival_proficiency": "none",
                                "learning_contexts": ["work", "english_class"],
                                "exposure_score": 34,
                                "last_year_practice_hours": 180,
                            },
                            {
                                "language": "spanish",
                                "spoken_proficiency": "native",
                                "reading_proficiency": "native",
                                "writing_proficiency": "professional",
                                "home_use": True,
                            },
                        ],
                    },
                    "adoption": {
                        "is_adopted": True,
                        "birth_parent_ethnicities": ["hispanic", "jewish"],
                        "birth_parent_cultures": ["hispanic", "jewish"],
                        "adoptive_parent_ethnicities": ["anglo"],
                        "adoptive_parent_cultures": ["anglo"],
                        "raised_cultures": ["anglo"],
                    },
                    "workplace_id": "plumbing-business-1",
                    "current_school_id": "college-1",
                    "education_history": {
                        "daycare_ids": ["daycare-1"],
                        "grade_school_ids": ["grade-school-1"],
                        "high_school_ids": ["high-school-1"],
                        "college_ids": ["college-1"],
                        "trade_school_ids": ["trade-school-1"],
                        "masters_university_ids": ["masters-1"],
                        "phd_university_ids": ["phd-1"],
                        "graduations": [
                            {
                                "institution_id": "high-school-1",
                                "graduation_year": 2007,
                                "credential": "diploma",
                                "discipline": "general",
                                "major": "general studies",
                                "skills": ["writing", "algebra"],
                            },
                            {
                                "institution_id": "trade-school-1",
                                "graduation_year": 2009,
                                "credential": "certificate",
                                "discipline": "skilled trades",
                                "major": "plumbing",
                                "skills": ["pipefitting", "water systems"],
                            },
                            {
                                "institution_id": "masters-1",
                                "graduation_year": 2018,
                                "credential": "MBA",
                                "discipline": "business",
                                "major": "business administration",
                                "skills": ["accounting", "operations management"],
                            }
                        ],
                    },
                    "employment_history": [
                        {
                            "workplace_id": "plumbing-shop-1",
                            "role": "plumber",
                            "start_year": 2009,
                            "end_year": 2016,
                            "employment_status": "employed",
                            "sector": "plumbing_services",
                            "skills_used": ["pipefitting", "water systems"],
                        },
                        {
                            "workplace_id": "plumbing-business-1",
                            "role": "plumbing business owner",
                            "start_year": 2019,
                            "employment_status": "business_owner",
                            "sector": "plumbing_services",
                            "skills_used": [
                                "plumbing",
                                "accounting",
                                "operations management",
                            ],
                        },
                    ],
                }
            ],
            "households": [
                {
                    "agent_id": "household-1",
                    "member_ids": ["person-1"],
                    "income_band": "middle",
                    "tenure": "owner",
                    "weight": 20,
                    "household_languages": ["spanish"],
                }
            ],
            "organizations": [
                {
                    "agent_id": "org-1",
                    "organization_type": "university",
                    "sector": "education",
                    "staff": 1200,
                },
                {
                    "agent_id": "plumbing-business-1",
                    "organization_type": "business",
                    "sector": "plumbing_services",
                    "display_name": "Jose Plumbing Services",
                    "owner_ids": ["person-1"],
                    "founded_year": 2019,
                    "customer_types": ["residents", "businesses"],
                    "service_languages": [
                        {
                            "language": "english",
                            "service_proficiency": "professional",
                            "staff_capacity": 4,
                        },
                        {
                            "language": "spanish",
                            "service_proficiency": "native",
                            "staff_capacity": 2,
                            "interpreter_capacity": 1,
                            "tags": ["customer_service"],
                        },
                    ],
                }
            ],
            "sector_market_balances": [
                {
                    "sector": "grocery",
                    "good_or_service": "fresh_food",
                    "local_demand": 1000,
                    "local_supply": 350,
                    "imports": 400,
                    "exports": 20,
                    "inventory_or_capacity_drawdown": 50,
                    "substitution": 100,
                    "unmet_demand": 120,
                    "price_pressure": 0.12,
                    "wait_pressure": 0.03,
                    "utilization": 0.97,
                    "notes": ["regional produce distributor"],
                }
            ],
            "inventories": [
                {
                    "holder_type": "household",
                    "holder_id": "household-1",
                    "sector": "household",
                    "good": "shelf_stable_food",
                    "quantity": 6,
                    "daily_use": 2,
                    "reorder_threshold_days": 5,
                    "reserve_target_days": 7,
                    "notes": ["pantry shelf"],
                },
                {
                    "holder_type": "organization",
                    "holder_id": "plumbing-business-1",
                    "sector": "grocery",
                    "good": "fresh_food",
                    "days_on_hand": 2,
                    "reorder_threshold_days": 3,
                    "reserve_target_days": 5,
                    "storage_type": "cold_chain",
                    "spoilage_risk": 0.25,
                    "stockout_risk": 0.7,
                },
            ],
            "pending_effects": [
                {
                    "source": "summer_blackout",
                    "target": "infrastructure_backlog",
                    "amount": 12000000,
                    "delay_turns": 1,
                    "duration_turns": 4,
                    "tags": ["grid", "capital_repair"],
                }
            ],
            "place_assets": [
                {
                    "name": "Downtown Clinic",
                    "asset_type": "clinic",
                    "services": [
                        {
                            "name": "Primary Care",
                            "service_type": "healthcare",
                            "capacity": 80,
                        }
                    ],
                }
            ],
            "neighborhoods": {
                "central": {
                    "housing_stock": {"rowhouse_units": 22},
                    "adjacent_sectors": ["government_center"],
                    "zoning": {
                        "allowed_uses": ["residential", "civic"],
                        "overlay_tags": ["historic_preservation"],
                        "max_housing_units": 900,
                        "historic_preservation_score": 0.65,
                    },
                    "place_assets": [
                        {
                            "name": "Central School",
                            "asset_type": "school",
                            "services": [
                                {
                                    "name": "K-8 Seats",
                                    "service_type": "education",
                                    "capacity": 500,
                                }
                            ],
                        }
                    ],
                }
            },
        }
    )

    path = save_city("roundtrip", city)

    assert path == tmp_path / "cities" / "roundtrip.json"
    assert load_city("roundtrip").population == 1234
    assert load_city("roundtrip").year == 2
    assert load_city("roundtrip").sensitivity.crime_unemployment == 1.25
    assert load_city("roundtrip").housing_assistance.shelter_beds == 12
    assert load_city("roundtrip").people[0].weight == 20
    assert load_city("roundtrip").people[0].parent_ids == (
        "birth-parent-1",
        "birth-parent-2",
    )
    assert load_city("roundtrip").people[0].identity.ethnicities == ("hispanic", "jewish")
    assert load_city("roundtrip").people[0].identity.cultures == ("anglo",)
    assert load_city("roundtrip").people[0].identity.affiliations[0].culture == "anglo"
    assert load_city("roundtrip").people[0].identity.affiliations[0].strength == (
        pytest.approx(0.7)
    )
    assert load_city("roundtrip").people[0].identity.affiliations[0].tags == ("household",)
    assert load_city("roundtrip").people[0].identity.strength_for("hispanic") == (
        pytest.approx(0.45)
    )
    assert load_city("roundtrip").people[0].language_profile.preferred_language == "spanish"
    assert load_city("roundtrip").people[0].language_profile.household_languages == (
        "spanish",
    )
    assert load_city("roundtrip").people[0].language_profile.interpreter_needed
    assert load_city("roundtrip").people[0].language_profile.skills[0].language == "english"
    assert (
        load_city("roundtrip").people[0].language_profile.skills[0].spoken_proficiency
        == "basic"
    )
    assert load_city("roundtrip").people[0].language_profile.skills[0].learning_contexts == (
        "work",
        "english_class",
    )
    assert load_city("roundtrip").people[0].language_profile.skills[1].home_use
    assert load_city("roundtrip").people[0].adoption.is_adopted
    assert load_city("roundtrip").people[0].adoption.raised_cultures == ("anglo",)
    assert load_city("roundtrip").people[0].workplace_id == "plumbing-business-1"
    assert load_city("roundtrip").people[0].current_school_id == "college-1"
    assert load_city("roundtrip").people[0].education_history.daycare_ids == ("daycare-1",)
    assert (
        load_city("roundtrip").people[0].education_history.graduations[0].institution_id
        == "high-school-1"
    )
    assert (
        load_city("roundtrip").people[0].education_history.graduations[0].graduation_year
        == 2007
    )
    assert load_city("roundtrip").people[0].education_history.graduations[0].skills == (
        "writing",
        "algebra",
    )
    assert (
        load_city("roundtrip").people[0].education_history.graduations[1].major
        == "plumbing"
    )
    assert (
        load_city("roundtrip").people[0].education_history.graduations[2].credential
        == "MBA"
    )
    assert load_city("roundtrip").people[0].employment_history[0].role == "plumber"
    assert load_city("roundtrip").people[0].employment_history[0].end_year == 2016
    assert (
        load_city("roundtrip").people[0].employment_history[1].employment_status
        == "business_owner"
    )
    assert load_city("roundtrip").households[0].member_ids == ("person-1",)
    assert load_city("roundtrip").households[0].household_languages == ("spanish",)
    assert load_city("roundtrip").organizations[0].organization_type == "university"
    assert load_city("roundtrip").organizations[1].owner_ids == ("person-1",)
    assert load_city("roundtrip").organizations[1].founded_year == 2019
    assert load_city("roundtrip").organizations[1].customer_types == (
        "residents",
        "businesses",
    )
    assert load_city("roundtrip").organizations[1].service_languages[1].language == "spanish"
    assert (
        load_city("roundtrip").organizations[1].service_languages[1].interpreter_capacity
        == 1
    )
    assert load_city("roundtrip").organizations[1].service_languages[1].tags == (
        "customer_service",
    )
    assert load_city("roundtrip").sector_market_balances[0].sector == "grocery"
    assert load_city("roundtrip").sector_market_balances[0].good_or_service == "fresh_food"
    assert load_city("roundtrip").sector_market_balances[0].accounted_supply == (
        pytest.approx(880)
    )
    assert load_city("roundtrip").sector_market_balances[0].effective_unmet_demand == (
        pytest.approx(120)
    )
    assert load_city("roundtrip").sector_market_balances[0].notes == (
        "regional produce distributor",
    )
    assert load_city("roundtrip").inventories[0].holder_type == "household"
    assert load_city("roundtrip").inventories[0].holder_id == "household-1"
    assert load_city("roundtrip").inventories[0].effective_days_on_hand == (
        pytest.approx(3)
    )
    assert load_city("roundtrip").inventories[1].raw_days_on_hand == pytest.approx(2)
    assert load_city("roundtrip").inventories[1].effective_days_on_hand == (
        pytest.approx(1.5)
    )
    assert load_city("roundtrip").inventories[1].cold_chain_dependent
    assert load_city("roundtrip").pending_effects[0].target == "infrastructure_backlog"
    assert load_city("roundtrip").pending_effects[0].tags == ("grid", "capital_repair")
    assert load_city("roundtrip").neighborhoods["central"].housing_stock.rowhouse_units == 22
    assert load_city("roundtrip").neighborhoods["central"].zoning.allowed_uses == (
        "residential",
        "civic",
    )
    assert load_city("roundtrip").neighborhoods["central"].zoning.overlay_tags == (
        "historic_preservation",
    )
    assert (
        load_city("roundtrip").neighborhoods["central"].zoning.historic_preservation_score
        == pytest.approx(0.65)
    )
    assert load_city("roundtrip").place_assets[0].service_capacity("healthcare") == 80
    assert (
        load_city("roundtrip")
        .neighborhoods["central"]
        .place_assets[0]
        .service_capacity("education")
        == 500
    )
