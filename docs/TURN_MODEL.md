# Turn Model

Last updated: 2026-08-18

City Simulator advances in yearly turns. A turn should be understandable as an
ordered sequence of civic changes, not a black-box formula.

The current source implementation exposes the annual pipeline as
`ANNUAL_TURN_STEPS`. Each step has a stable name plus declared `requires` and
`produces` fields so dependencies remain visible as the model grows.

For the broader design process for adding new turn domains, see
[`TURN_PROCESS_MODEL.md`](TURN_PROCESS_MODEL.md).

## Turn Inputs

Each turn starts from:

- the current `CityState`;
- one `CityPolicy`;
- `ExternalControls` from county, state, country, and regional context;
- `ModelParameters` for formula coefficients;
- city sensitivity traits;
- previous active issues;
- pending delayed effects;
- optional people, households, organizations, neighborhoods, and place assets.

## Current Source Order

The current annual turn order is:

```text
validate_inputs
-> local_fiscal_policy
-> development_and_jobs
-> infrastructure_environment
-> seasonal_signals
-> satisfaction_migration_demographics
-> labor_market
-> sentiment
-> commit_state
-> detect_issues
```

## Turn Phases

### 1. Validate Inputs

Validates policy bounds and captures the previous active issues so the report
can later identify which issues were overcome.

Produces:

- `previous_issues`

### 2. Local Fiscal Policy

Computes city revenue, expenses, and budget from tax policy, tax base, service
costs, investments, debt service, and outside funding.

Produces:

- `revenue`
- `expenses`
- `budget`

### 3. Development And Jobs

Computes housing and job changes from housing investment, county directives,
zoning, permitting speed, development restrictions, business support,
infrastructure quality, tax drag, and national unemployment effects.

Produces:

- `housing_units`
- `jobs_delta`
- `jobs`

### 4. Infrastructure And Environment

Updates infrastructure and pollution. Transit and service investment improve
infrastructure; annual wear lowers it. Population and job growth add pollution;
environment spending and state mandates reduce pollution.

Requires:

- `jobs_delta`

Produces:

- `infrastructure`
- `pollution`

### 5. Seasonal Signals

Computes the housing gap and builds the `SignalLedger` for the turn.

Current signal concepts:

- `seasonal_heat_cascade`
- `language_service_access`
- `sector_market_balance`

The signal system is intentionally broader than pressure. A signal can be a
need, flow, capacity, balance, risk, buffer, service gap, import dependency, or
pressure. Domain modules should add modular `SignalConcept` collectors rather
than hard-coding every channel into the turn step.

Requires:

- `housing_units`
- `infrastructure`
- `pollution`

Produces:

- `housing_gap`
- `signal_ledger`

### 6. Satisfaction, Migration, And Demographics

Computes satisfaction, population change, the new population total, updated
demographic cohorts, and growth rate. Satisfaction responds to services,
infrastructure, taxes, pollution, housing gap, restrictions, and budget stress.
Population responds to satisfaction, housing drag, local influx/outflux rates,
federal growth effects, tax migration drag, and development restrictions.

Requires:

- `infrastructure`
- `pollution`
- `housing_gap`

Produces:

- `satisfaction`
- `population_delta`
- `population`
- `demographics`
- `growth_rate`

### 7. Labor Market

Computes labor force, resident employment, unemployment, job vacancies,
commuters into the city, commuters out of the city, and participation and
unemployment rates.

The source model distinguishes jobs located in the city from resident
employment. Future regional labor-market work should reconcile suitable local
jobs, remote work, nearby-city jobs, relocation, and unemployment.

Requires:

- `population`
- `demographics`
- `jobs`
- `infrastructure`

Produces:

- `labor_market`

### 8. Sentiment

Computes crime, sentiment component signals, and public sentiment.

Public sentiment is derived from multiple components rather than copied from
satisfaction. Current sentiment components include surveys, migration behavior,
business behavior, consumer spending, savings security, housing stress, safety,
services, civic trust, and future confidence. The step can consume
`SignalLedger` channels such as heat, grid, healthcare, civic trust, and
language access signals.

Requires:

- `jobs_delta`
- `pollution`
- `housing_gap`
- `signal_ledger`
- `satisfaction`
- `population`
- `demographics`
- `growth_rate`
- `labor_market`

Produces:

- `crime`
- `sentiment_signals`
- `public_sentiment`

### 9. Commit State

Builds the next `CityState`, stores the derived `CityMetrics`, advances pending
delayed effects, and adds new delayed effects created from turn signals.

Requires the fiscal, development, infrastructure, signal, satisfaction,
population, labor, crime, and sentiment intermediates.

Produces:

- `next_state`

### 10. Detect Issues

Detects active issues from the committed next state and the turn's
`SignalLedger`. Compares current issues against the previous issue set so
`YearResult` can report active and overcome issues.

Requires:

- `next_state`
- `signal_ledger`

Produces:

- `active_issues`

## Turn Output

`advance_year()` returns a `YearResult` containing:

- year;
- next `CityState`;
- revenue and expenses;
- population delta;
- jobs delta;
- housing gap;
- active issues;
- overcome issues;
- `signal_ledger`.

The committed state also includes `CityMetrics` such as happiness, public
sentiment, crime, growth rate, labor force, employed residents, unemployed
residents, jobs in city, vacancies, commuters, housing pressure, density, and
service coverage.

## Signal Concepts

Signal collection lives in `signals.py`.

Each `SignalConcept` declares:

- `name`
- `need`
- `inputs`
- `outputs`
- `channels`
- `collect`

This declaration is part of the object model. A new domain should be able to
state why it exists, which inputs it consumes, which outputs it produces, and
which signal channels it registers.

Current examples:

- `seasonal_heat_cascade` consumes population, demographics, physical profile,
  neighborhoods, service capacity, delayed effects, environmental investment,
  infrastructure, and pollution. It emits heat exposure, cooling demand, grid
  shortfall, healthcare surge, and civic trust risk channels.
- `language_service_access` consumes people language profiles and organization
  service languages. It emits service-access gap, limited-access share,
  interpreter need, and multilingual bridge capacity channels.
- `sector_market_balance` consumes `CityState.sector_market_balances`. It
  emits local supply gaps, regional import dependency, unmet demand, price
  pressure, wait pressure, and capacity strain channels.

## Delayed Effects

Signals that should persist beyond the current turn can become `DelayedEffect`
records on `CityState.pending_effects`.

A delayed effect stores:

- source;
- target channel;
- amount;
- delay;
- duration;
- decay;
- tags;
- explanation.

Use delayed effects for intermediate channels, not as shortcuts directly to
headline metrics.

Good:

```text
summer_blackout -> civic_trust / healthcare_surge / repair_backlog
```

Bad:

```text
summer_blackout -> happiness -10
```

## Design Rules

- Keep turns deterministic by default.
- Treat turn order as an explicit causal contract.
- A step should consume only prior step outputs, current canonical state,
  policy inputs, external controls, model parameters, or declared delayed
  effects.
- Prefer named intermediate values and signal channels over hidden direct
  metric changes.
- Add new domain behavior through views, signal concepts, and turn steps with
  declared inputs and outputs.
- Keep top-level metrics as derived outputs. Starter or scenario files may
  provide initial values, but later turns should derive values from lower-level
  state whenever practical.
- Do not require every entity, visitor, shipment, or relationship to be fully
  materialized before the city can run. Use aggregate fallback models and add
  explicit records where detail matters.
