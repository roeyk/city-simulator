from city_simulator import (
    CityPolicy,
    CityState,
    advance_citizen_histories,
    generate_representative_citizens,
    simulate,
)


def test_representative_citizens_are_deterministic():
    first = generate_representative_citizens(CityState(), count=5, seed=3)
    second = generate_representative_citizens(CityState(), count=5, seed=3)

    assert first == second
    assert len(first) == 5


def test_citizen_histories_advance_with_simulation_results():
    citizens = generate_representative_citizens(CityState(), count=3)
    results = simulate(CityState(), CityPolicy(), 2)

    advanced = advance_citizen_histories(citizens, results)

    assert all(citizen.age == original.age + 2 for citizen, original in zip(advanced, citizens))
    assert all(len(citizen.history) == 3 for citizen in advanced)
    assert all("Year 2:" in citizen.history[-1] for citizen in advanced)
