import pytest

from city_simulator import (
    CityState,
    HouseholdAgent,
    OrganizationAgent,
    Parcel,
    ParcelGrid,
    ParcelOccupancy,
    parcel_commute_minutes,
    parcel_grid_distance,
    parcel_shipping_cost,
)
from city_simulator.scenario import (
    ScenarioError,
    city_from_mapping,
    load_city,
    save_city,
)


def test_sparse_square_parcel_grid_measures_distance_and_costs():
    city = CityState(
        parcel_grid=ParcelGrid(
            width=1000,
            height=1000,
            cell_size_miles=0.2,
            commute_minutes_per_grid_step=3.0,
            shipping_cost_per_grid_step=2.5,
        ),
        parcels={
            "home": Parcel("home", grid_x=1, grid_y=1),
            "work": Parcel("work", grid_x=5, grid_y=3),
            "warehouse": Parcel("warehouse", grid_x=8, grid_y=1),
        },
    )

    assert parcel_grid_distance(city, "home", "work") == 6
    assert parcel_commute_minutes(city, "home", "work") == pytest.approx(18)
    assert parcel_shipping_cost(city, "warehouse", "work", base_cost=10) == pytest.approx(22.5)


def test_default_sparse_square_grid_has_million_parcel_coordinate_space():
    grid = ParcelGrid()

    assert grid.grid_type == "square"
    assert grid.width == 1000
    assert grid.height == 1000


def test_parcels_hold_multiple_agent_and_asset_occupants():
    parcel = Parcel(
        "downtown-001",
        grid_x=10,
        grid_y=4,
        neighborhood="downtown",
        land_use="mixed_use",
        occupancy=ParcelOccupancy(
            person_ids=("person-1", "person-2"),
            household_ids=("household-1",),
            organization_ids=("clinic-1", "grocery-1"),
            place_asset_ids=("building-1",),
            infrastructure_ids=("feeder-1", "water-main-1"),
        ),
    )
    city = CityState(
        parcels={"downtown-001": parcel},
        households=(
            HouseholdAgent(
                "household-1",
                member_ids=("person-1", "person-2"),
                income_band="middle",
                parcel_id="downtown-001",
            ),
        ),
        organizations=(
            OrganizationAgent(
                "clinic-1",
                organization_type="clinic",
                parcel_id="downtown-001",
            ),
        ),
    )

    assert city.parcels["downtown-001"].occupancy.household_ids == ("household-1",)
    assert city.households[0].parcel_id == "downtown-001"
    assert city.organizations[0].parcel_id == "downtown-001"


def test_city_from_mapping_reads_sparse_square_parcels_and_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("CITY_SIMULATOR_HOME", str(tmp_path))
    city = city_from_mapping(
        {
            "parcel_grid": {
                "grid_type": "square",
                "width": 1000,
                "height": 1000,
                "cell_size_miles": 0.25,
                "origin_label": "southwest corner",
                "commute_minutes_per_grid_step": 4,
                "shipping_cost_per_grid_step": 3,
            },
            "neighborhoods": {
                "downtown": {
                    "parcel_ids": ["p-1", "p-2"],
                    "zoning": {"allowed_uses": ["mixed_use", "civic"]},
                }
            },
            "parcels": {
                "p-1": {
                    "grid_x": 0,
                    "grid_y": 0,
                    "neighborhood": "downtown",
                    "land_use": "mixed_use",
                    "area_acres": 1.4,
                    "max_housing_units": 80,
                    "max_jobs": 120,
                    "overlays": ["transit_oriented_development"],
                    "occupancy": {
                        "household_ids": ["household-1"],
                        "organization_ids": ["org-1"],
                    },
                },
            "p-2": {
                "grid_x": 4,
                "grid_y": 2,
                "neighborhood": "downtown",
                "land_use": "industrial",
                "natural_cover": "river",
                "development_stage": "partly_developed",
                "occupancy": {"infrastructure_ids": ["road-segment-1"]},
            },
            },
        }
    )

    saved_path = save_city("parcel-test", city)
    loaded = load_city(saved_path)

    assert loaded.parcel_grid.width == 1000
    assert loaded.neighborhoods["downtown"].parcel_ids == ("p-1", "p-2")
    assert loaded.parcels["p-1"].parcel_id == "p-1"
    assert loaded.parcels["p-1"].zoning.allowed_uses == ("residential",)
    assert loaded.parcels["p-1"].occupancy.organization_ids == ("org-1",)
    assert loaded.parcels["p-2"].natural_cover == "river"
    assert loaded.parcels["p-2"].development_stage == "partly_developed"
    assert loaded.parcels["p-2"].occupancy.infrastructure_ids == ("road-segment-1",)
    assert parcel_commute_minutes(loaded, "p-1", "p-2") == pytest.approx(24)


def test_city_from_mapping_rejects_invalid_parcel_shapes():
    with pytest.raises(ScenarioError, match="city parcels must be an object"):
        city_from_mapping({"parcels": []})

    with pytest.raises(ScenarioError, match="parcel p-1 occupancy must be an object"):
        city_from_mapping({"parcels": {"p-1": {"grid_x": 0, "grid_y": 0, "occupancy": []}}})


def test_distance_helpers_reject_out_of_bounds_parcels():
    city = CityState(
        parcel_grid=ParcelGrid(width=1000, height=1000),
        parcels={
            "inside": Parcel("inside", grid_x=999, grid_y=999),
            "outside": Parcel("outside", grid_x=1000, grid_y=0),
        },
    )

    with pytest.raises(ValueError, match="grid_x is outside parcel grid"):
        parcel_grid_distance(city, "inside", "outside")
