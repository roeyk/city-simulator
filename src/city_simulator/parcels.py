from __future__ import annotations

from math import ceil, sqrt

from city_simulator.state import CityState, Parcel, ParcelGrid

SQUARE_METERS_PER_SQUARE_KILOMETER = 1_000_000.0
SQUARE_METERS_PER_SQUARE_MILE = 2_589_988.110336


def square_parcel_grid_for_area(
    *,
    area_square_miles: float | None = None,
    area_square_km: float | None = None,
    cell_size_meters: float = 20.0,
) -> tuple[int, int]:
    total_cells = parcel_coordinate_capacity_for_area(
        area_square_miles=area_square_miles,
        area_square_km=area_square_km,
        cell_size_meters=cell_size_meters,
    )
    side = ceil(sqrt(total_cells))
    return (side, side)


def parcel_grid_for_area(
    *,
    area_square_miles: float | None = None,
    area_square_km: float | None = None,
    cell_size_meters: float = 20.0,
    grid_type: str = "square",
    origin_label: str = "",
    commute_minutes_per_grid_step: float = 2.5,
    shipping_cost_per_grid_step: float = 1.25,
) -> ParcelGrid:
    if grid_type != "square":
        raise ValueError(f"unsupported parcel grid type for area sizing: {grid_type}")
    width, height = square_parcel_grid_for_area(
        area_square_miles=area_square_miles,
        area_square_km=area_square_km,
        cell_size_meters=cell_size_meters,
    )
    return ParcelGrid(
        grid_type=grid_type,
        width=width,
        height=height,
        cell_size_meters=cell_size_meters,
        origin_label=origin_label,
        commute_minutes_per_grid_step=commute_minutes_per_grid_step,
        shipping_cost_per_grid_step=shipping_cost_per_grid_step,
    )


def parcel_coordinate_capacity_for_area(
    *,
    area_square_miles: float | None = None,
    area_square_km: float | None = None,
    cell_size_meters: float = 20.0,
) -> int:
    area_square_meters = _area_square_meters(area_square_miles, area_square_km)
    if cell_size_meters <= 0:
        raise ValueError("cell_size_meters must be positive")
    return max(ceil(area_square_meters / (cell_size_meters**2)), 1)


def parcel_grid_distance(state: CityState, origin_id: str, destination_id: str) -> float:
    origin = _parcel(state, origin_id)
    destination = _parcel(state, destination_id)
    _validate_grid(state)
    _validate_parcel_coordinate(state, origin)
    _validate_parcel_coordinate(state, destination)
    return abs(origin.grid_x - destination.grid_x) + abs(origin.grid_y - destination.grid_y)


def parcel_commute_minutes(state: CityState, origin_id: str, destination_id: str) -> float:
    return (
        parcel_grid_distance(state, origin_id, destination_id)
        * state.parcel_grid.commute_minutes_per_grid_step
    )


def parcel_shipping_cost(
    state: CityState,
    origin_id: str,
    destination_id: str,
    *,
    base_cost: float = 0.0,
) -> float:
    return base_cost + (
        parcel_grid_distance(state, origin_id, destination_id)
        * state.parcel_grid.shipping_cost_per_grid_step
    )


def _parcel(state: CityState, parcel_id: str) -> Parcel:
    try:
        return state.parcels[parcel_id]
    except KeyError as exc:
        raise KeyError(f"unknown parcel: {parcel_id}") from exc


def _area_square_meters(
    area_square_miles: float | None,
    area_square_km: float | None,
) -> float:
    if (area_square_miles is None) == (area_square_km is None):
        raise ValueError("provide exactly one of area_square_miles or area_square_km")
    if area_square_miles is not None:
        if area_square_miles <= 0:
            raise ValueError("area_square_miles must be positive")
        return area_square_miles * SQUARE_METERS_PER_SQUARE_MILE
    if area_square_km is None:
        raise ValueError("provide exactly one of area_square_miles or area_square_km")
    if area_square_km <= 0:
        raise ValueError("area_square_km must be positive")
    return area_square_km * SQUARE_METERS_PER_SQUARE_KILOMETER


def _validate_grid(state: CityState) -> None:
    if state.parcel_grid.grid_type != "square":
        raise ValueError(
            f"unsupported parcel grid type for distance calculations: {state.parcel_grid.grid_type}"
        )
    if state.parcel_grid.width <= 0 or state.parcel_grid.height <= 0:
        raise ValueError("parcel grid width and height must be positive")


def _validate_parcel_coordinate(state: CityState, parcel: Parcel) -> None:
    if not 0 <= parcel.grid_x < state.parcel_grid.width:
        raise ValueError(f"parcel {parcel.parcel_id} grid_x is outside parcel grid")
    if not 0 <= parcel.grid_y < state.parcel_grid.height:
        raise ValueError(f"parcel {parcel.parcel_id} grid_y is outside parcel grid")
