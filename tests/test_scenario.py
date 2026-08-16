import pytest

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
    assert load_city("roundtrip").pending_effects[0].target == "infrastructure_backlog"
    assert load_city("roundtrip").pending_effects[0].tags == ("grid", "capital_repair")
    assert load_city("roundtrip").neighborhoods["central"].housing_stock.rowhouse_units == 22
    assert load_city("roundtrip").place_assets[0].service_capacity("healthcare") == 80
    assert (
        load_city("roundtrip")
        .neighborhoods["central"]
        .place_assets[0]
        .service_capacity("education")
        == 500
    )
