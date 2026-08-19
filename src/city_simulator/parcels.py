from __future__ import annotations

from city_simulator.state import CityState, Parcel


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


def _validate_grid(state: CityState) -> None:
    if state.parcel_grid.grid_type != "square":
        raise ValueError(f"unsupported parcel grid type: {state.parcel_grid.grid_type}")
    if state.parcel_grid.width <= 0 or state.parcel_grid.height <= 0:
        raise ValueError("parcel grid width and height must be positive")


def _validate_parcel_coordinate(state: CityState, parcel: Parcel) -> None:
    if not 0 <= parcel.grid_x < state.parcel_grid.width:
        raise ValueError(f"parcel {parcel.parcel_id} grid_x is outside parcel grid")
    if not 0 <= parcel.grid_y < state.parcel_grid.height:
        raise ValueError(f"parcel {parcel.parcel_id} grid_y is outside parcel grid")
