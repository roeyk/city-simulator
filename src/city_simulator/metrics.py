from __future__ import annotations

from city_simulator.derived import (
    _active_effect_amount,
    _clamp,
    _density,
    _service_coverage,
)
from city_simulator.state import (
    CityMetrics,
    CitySensitivity,
    CityState,
    Demographics,
    ModelParameters,
    SignalLedger,
)


def _city_metrics(
    state: CityState,
    population: float,
    demographics: Demographics,
    jobs: float,
    jobs_delta: float,
    housing_units: float,
    housing_gap: float,
    satisfaction: float,
    infrastructure: float,
    pollution: float,
    growth_rate: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
    signal_ledger: SignalLedger | None = None,
    labor_market: dict[str, float] | None = None,
    crime: float | None = None,
    sentiment_signals: dict[str, float] | None = None,
    public_sentiment: float | None = None,
) -> CityMetrics:
    ledger = signal_ledger or SignalLedger()
    service_coverage = _service_coverage(state)
    labor = labor_market or _labor_market(
        population=population,
        demographics=demographics,
        jobs=jobs,
        infrastructure=infrastructure,
        education_profile=state.population_profile.get("education_percent", {}),
        parameters=parameters,
        sensitivity=sensitivity,
    )
    unemployment_rate = labor["unemployment_rate"]
    housing_pressure = max(housing_gap, 0.0) / max(population, 1.0)
    density = _density(population, state)
    crime_score = (
        crime
        if crime is not None
        else _crime(
            satisfaction=satisfaction,
            pollution=pollution,
            unemployment_rate=unemployment_rate,
            housing_pressure=housing_pressure,
            service_coverage=service_coverage,
            parameters=parameters,
            sensitivity=sensitivity,
        )
    )
    signals = (
        sentiment_signals
        if sentiment_signals is not None
        else _sentiment_signals(
            state=state,
            demographics=demographics,
            satisfaction=satisfaction,
            growth_rate=growth_rate,
            jobs_delta=jobs_delta,
            pollution=pollution,
            unemployment_rate=unemployment_rate,
            job_vacancy_rate=labor["job_vacancy_rate"],
            crime=crime_score,
            housing_pressure=housing_pressure,
            service_coverage=service_coverage,
            parameters=parameters,
            sensitivity=sensitivity,
            signal_ledger=ledger,
        )
    )
    sentiment = (
        public_sentiment
        if public_sentiment is not None
        else _public_sentiment(signals, parameters)
    )
    return CityMetrics(
        happiness=satisfaction,
        public_sentiment=sentiment,
        crime=crime_score,
        growth_rate=growth_rate,
        labor_force=labor["labor_force"],
        employed_residents=labor["employed_residents"],
        unemployed_residents=labor["unemployed_residents"],
        jobs_in_city=jobs,
        job_vacancies=labor["job_vacancies"],
        commuters_in=labor["commuters_in"],
        commuters_out=labor["commuters_out"],
        labor_force_participation_rate=labor["labor_force_participation_rate"],
        unemployment_rate=unemployment_rate,
        housing_pressure=housing_pressure,
        density_per_square_mile=density,
        service_coverage=service_coverage,
        sentiment_signals=signals,
    )


def _labor_market(
    population: float,
    demographics: Demographics,
    jobs: float,
    infrastructure: float,
    education_profile: dict[str, float],
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> dict[str, float]:
    high_income_share = demographics.high_income / max(population, 1.0)
    low_income_share = demographics.low_income / max(population, 1.0)
    education_drag = _education_mismatch(education_profile, parameters)
    participation_rate = _clamp(
        parameters.base_labor_participation
        + high_income_share * parameters.high_income_labor_participation_bonus
        - low_income_share * parameters.low_income_labor_participation_drag,
        0.52,
        0.78,
    )
    labor_force = demographics.working_age * participation_rate
    access_score = _clamp(
        parameters.base_job_access
        + infrastructure
        / parameters.infrastructure_job_access_divisor
        * sensitivity.labor_access_infrastructure
        - education_drag * sensitivity.labor_access_education
        - low_income_share
        * parameters.low_income_job_access_drag
        * sensitivity.labor_access_income,
        0.42,
        0.94,
    )
    resident_accessible_jobs = jobs * access_score
    employed_residents = min(labor_force, resident_accessible_jobs)
    unemployed_residents = max(labor_force - employed_residents, 0.0)
    remaining_city_jobs = max(jobs - employed_residents, 0.0)
    commuter_fill_rate = _clamp(
        parameters.commuter_fill_base
        + education_drag * parameters.commuter_fill_education_bonus,
        0.12,
        0.55,
    )
    commuters_in = min(remaining_city_jobs, jobs * commuter_fill_rate)
    job_vacancies = max(remaining_city_jobs - commuters_in, 0.0)
    commuters_out = max(employed_residents - jobs, 0.0)
    return {
        "labor_force": labor_force,
        "employed_residents": employed_residents,
        "unemployed_residents": unemployed_residents,
        "jobs_in_city": jobs,
        "job_vacancies": job_vacancies,
        "commuters_in": commuters_in,
        "commuters_out": commuters_out,
        "labor_force_participation_rate": participation_rate,
        "unemployment_rate": unemployed_residents / max(labor_force, 1.0),
        "job_vacancy_rate": job_vacancies / max(jobs, 1.0),
    }


def _education_mismatch(
    education_profile: dict[str, float],
    parameters: ModelParameters | None = None,
) -> float:
    model_parameters = parameters or ModelParameters()
    if not education_profile:
        return model_parameters.default_education_mismatch
    less_than_high_school = education_profile.get("less_than_high_school", 0.0)
    high_school = education_profile.get("high_school", 0.0)
    college_or_higher = (
        education_profile.get("bachelors", 0.0)
        + education_profile.get("graduate", 0.0)
        + education_profile.get("college_or_higher", 0.0)
    )
    return _clamp(
        less_than_high_school / 180
        + high_school / 450
        - college_or_higher / 700,
        0.02,
        0.18,
    )


def _crime(
    satisfaction: float,
    pollution: float,
    unemployment_rate: float,
    housing_pressure: float,
    service_coverage: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
) -> float:
    return _clamp(
        parameters.base_crime
        + unemployment_rate
        * parameters.crime_unemployment_multiplier
        * sensitivity.crime_unemployment
        + housing_pressure * parameters.crime_housing_multiplier * sensitivity.crime_housing
        + max(50.0 - satisfaction, 0.0) * parameters.crime_low_satisfaction_multiplier
        + max(pollution - 55.0, 0.0) * parameters.crime_pollution_multiplier
        - service_coverage * parameters.crime_service_mitigation * sensitivity.crime_services,
        0.0,
        100.0,
    )


def _sentiment_signals(
    state: CityState,
    demographics: Demographics,
    satisfaction: float,
    growth_rate: float,
    jobs_delta: float,
    pollution: float,
    unemployment_rate: float,
    job_vacancy_rate: float,
    crime: float,
    housing_pressure: float,
    service_coverage: float,
    parameters: ModelParameters,
    sensitivity: CitySensitivity,
    signal_ledger: SignalLedger | None = None,
) -> dict[str, float]:
    ledger = signal_ledger or SignalLedger()
    current_population = max(demographics.total, 1.0)
    low_income_share = demographics.low_income / current_population
    high_income_share = demographics.high_income / current_population
    budget_stability = (
        100.0
        if state.budget >= 0
        else _clamp(70.0 + state.budget / 2_000_000, 0.0, 70.0)
    )
    return {
        "survey": satisfaction,
        "migration_behavior": _clamp(
            50.0 + growth_rate * 1_200 * sensitivity.sentiment_migration,
            0.0,
            100.0,
        ),
        "business_behavior": _clamp(
            54.0
            + jobs_delta / 250 * sensitivity.sentiment_business
            - unemployment_rate * 85
            - job_vacancy_rate * 35,
            0.0,
            100.0,
        ),
        "consumer_spending": _clamp(
            45.0
            + satisfaction * 0.35
            - unemployment_rate * 90 * sensitivity.sentiment_financial_stress
            - housing_pressure * 120,
            0.0,
            100.0,
        ),
        "savings_security": _clamp(
            72.0
            - low_income_share * 35 * sensitivity.sentiment_financial_stress
            + high_income_share * 12
            - unemployment_rate * 120 * sensitivity.sentiment_financial_stress,
            0.0,
            100.0,
        ),
        "housing_stress": _clamp(100.0 - housing_pressure * 520, 0.0, 100.0),
        "safety": _clamp(100.0 - crime, 0.0, 100.0),
        "services": service_coverage,
        "civic_trust": _clamp(
            satisfaction * 0.35
            + service_coverage * 0.3
            + budget_stability * 0.2
            + (100.0 - crime) * 0.15
            + _active_effect_amount(state, "civic_trust")
            - ledger.get("civic_trust_risk"),
            0.0,
            100.0,
        ),
        "future_confidence": _clamp(
            52.0 + growth_rate * 800 + jobs_delta / 280 - unemployment_rate * 95 - pollution * 0.12,
            0.0,
            100.0,
        ),
    }


def _public_sentiment(signals: dict[str, float], parameters: ModelParameters) -> float:
    weights = parameters.public_sentiment_weights
    return sum(signals[key] * weight for key, weight in weights.items())
