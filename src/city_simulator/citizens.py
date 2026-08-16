from __future__ import annotations

from dataclasses import dataclass

from city_simulator.model import CityState, YearResult


@dataclass(frozen=True)
class Citizen:
    id: str
    age: int
    income_group: str
    employed: bool
    housed: bool
    satisfaction: float
    history: tuple[str, ...] = ()


def generate_representative_citizens(
    state: CityState,
    count: int = 25,
    seed: int = 0,
) -> list[Citizen]:
    if count < 0:
        raise ValueError("count must be non-negative")
    return [_citizen_for_slot(state, index, seed) for index in range(count)]


def advance_citizen_histories(
    citizens: list[Citizen],
    results: list[YearResult],
) -> list[Citizen]:
    current = citizens
    for result in results:
        current = [_advance_citizen(citizen, result) for citizen in current]
    return current


def _citizen_for_slot(state: CityState, index: int, seed: int) -> Citizen:
    total = max(state.population, 1.0)
    age_roll = _roll(index, seed, 17)
    income_roll = _roll(index, seed, 31)
    employed_roll = _roll(index, seed, 43)
    housed_roll = _roll(index, seed, 59)

    children_share = state.demographics.children / total
    working_share = state.demographics.working_age / total
    if age_roll < children_share:
        age = 5 + int(age_roll / max(children_share, 0.001) * 12)
    elif age_roll < children_share + working_share:
        relative = (age_roll - children_share) / max(working_share, 0.001)
        age = 18 + int(relative * 46)
    else:
        seniors_share = max(1.0 - children_share - working_share, 0.001)
        relative = (age_roll - children_share - working_share) / seniors_share
        age = 65 + int(min(relative, 1.0) * 25)

    low_share = state.demographics.low_income / total
    middle_share = state.demographics.middle_income / total
    if income_roll < low_share:
        income_group = "low"
    elif income_roll < low_share + middle_share:
        income_group = "middle"
    else:
        income_group = "high"

    working_age = 18 <= age < 65
    employment_rate = min(state.jobs / max(state.demographics.working_age, 1.0), 1.0)
    housed_rate = min(state.housing_units * 2.35 / total, 1.0)
    employed = working_age and employed_roll < employment_rate
    housed = housed_roll < housed_rate
    return Citizen(
        id=f"citizen-{seed}-{index}",
        age=age,
        income_group=income_group,
        employed=employed,
        housed=housed,
        satisfaction=state.satisfaction,
        history=(f"Year {state.year}: entered record as a {income_group}-income resident.",),
    )


def _advance_citizen(citizen: Citizen, result: YearResult) -> Citizen:
    age = citizen.age + 1
    employed = _updated_employment(citizen, result)
    housed = _updated_housing(citizen, result)
    satisfaction = _citizen_satisfaction(citizen, result, employed, housed)
    return Citizen(
        id=citizen.id,
        age=age,
        income_group=citizen.income_group,
        employed=employed,
        housed=housed,
        satisfaction=satisfaction,
        history=citizen.history + (_history_line(citizen, result, employed, housed, satisfaction),),
    )


def _updated_employment(citizen: Citizen, result: YearResult) -> bool:
    if not 18 <= citizen.age < 65:
        return False
    if result.jobs_delta > 0 and not citizen.employed:
        return _stable_choice(citizen.id, result.year, 5)
    if result.jobs_delta < 0 and citizen.employed:
        return not _stable_choice(citizen.id, result.year, 7)
    return citizen.employed


def _updated_housing(citizen: Citizen, result: YearResult) -> bool:
    if result.housing_gap < 0 and not citizen.housed:
        return _stable_choice(citizen.id, result.year, 3)
    if result.housing_gap > result.state.population * 0.05 and citizen.housed:
        return not _stable_choice(citizen.id, result.year, 11)
    return citizen.housed


def _citizen_satisfaction(
    citizen: Citizen,
    result: YearResult,
    employed: bool,
    housed: bool,
) -> float:
    value = result.state.satisfaction
    if 18 <= citizen.age < 65 and not employed:
        value -= 12
    if not housed:
        value -= 18
    if citizen.income_group == "low":
        value -= 4
    elif citizen.income_group == "high":
        value += 3
    return max(0.0, min(value, 100.0))


def _history_line(
    citizen: Citizen,
    result: YearResult,
    employed: bool,
    housed: bool,
    satisfaction: float,
) -> str:
    changes: list[str] = []
    if employed and not citizen.employed:
        changes.append("found work")
    elif citizen.employed and not employed:
        changes.append("lost work")
    if housed and not citizen.housed:
        changes.append("found housing")
    elif citizen.housed and not housed:
        changes.append("lost housing")
    if not changes:
        changes.append("saw city conditions shift")
    issues = ", ".join(issue.name for issue in result.active_issues) or "no major active issues"
    return (
        f"Year {result.year}: {', '.join(changes)}; "
        f"satisfaction {satisfaction:.1f}; city issues: {issues}."
    )


def _roll(index: int, seed: int, salt: int) -> float:
    value = (index + 1) * 1_103_515_245 + seed * 12_345 + salt * 97
    return value % 10_000 / 10_000


def _stable_choice(identifier: str, year: int, salt: int) -> bool:
    value = sum(ord(char) for char in identifier) + year * 131 + salt * 17
    return value % 5 == 0
