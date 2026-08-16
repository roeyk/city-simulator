# Turn Model

Last updated: 2026-08-15

City Simulator advances in yearly turns. A turn should be understandable as a
sequence of civic changes, not a black-box formula.

The yearly turn is the public resolution for scenario comparison, but it does
not require every cause to be averaged into one annual value. A turn can contain
representative seasonal periods and bounded feedback passes before committing
the next yearly state.

## Turn Inputs

Each turn starts from:

- the current city state;
- one city policy package;
- outside controls from county, state, and country;
- model parameters that hold tunable formula coefficients;
- city sensitivity traits that modify how strongly the city reacts to pressures;
- previous active issues;
- optional representative citizen records.

## Turn Phases

The source implementation exposes the annual pipeline as `ANNUAL_TURN_STEPS`.
Each step has a stable name plus declared `requires` and `produces` fields so
future systems can add causal layers without hiding the turn order inside one
large function.

1. Outside pressure

   County, state, and country inputs affect the city before local outcomes are
   calculated. Examples include intergovernmental funding, housing directives,
   state service or environment mandates, national interest rates, growth
   pressure, and national unemployment pressure.

2. Local fiscal policy

   City taxes and the tax base produce revenue. City spending, baseline resident
   service cost, and financing cost produce expenses. The budget is updated.

3. Development and jobs

   Housing investment, county housing directives, zoning restrictiveness,
   permitting speed, and development restrictions determine new housing units.
   Business support, infrastructure quality, taxes, development restrictions,
   and national unemployment pressure determine job change.

4. Labor market

   The city distinguishes jobs located in the city from resident employment.
   Working-age population produces a labor force through participation rates.
   Residents fill the city jobs they can realistically access, while mismatch
   can leave both unemployed residents and unfilled jobs. The turn also derives
   job vacancies, commuters into the city, commuters out of the city, and the
   unemployment rate.

5. Infrastructure and environment

   Transit and services improve infrastructure while annual wear lowers it.
   Population and job growth add pollution pressure. City environment spending
   and state environmental mandates reduce pollution. Seasonal pressures such
   as heat, snow, storms, drought, flooding, smoke, pests, or allergy seasons
   should be represented as sub-annual exposure profiles that roll into the
   yearly result.

6. Satisfaction and migration

   Satisfaction responds to services, infrastructure, taxes, pollution, housing
   pressure, restrictions, and budget stress. Population then changes through
   satisfaction, housing drag, local influx/outflux rates, federal growth
   pressure, tax migration drag, and development restrictions.

7. Demographics

   Age and income cohorts advance from the new population total. For now this is
   aggregate and deterministic; richer cohort mechanics should come later.

8. Sentiment

   Public sentiment is derived from multiple signals rather than copied from
   satisfaction. Current signal channels include surveys, migration behavior,
   business behavior, consumer spending, savings security, housing stress,
   safety, services, civic trust, and future confidence.

9. Issues and resolutions

   The simulator detects active issues from the new city state and compares them
   with the previous year's issues to identify what was overcome. If an
   internal feedback loop does not stabilize within the annual turn's capped
   feedback passes, the unresolved cascade should become an active issue or
   model warning rather than being silently hidden.

10. Citizen histories

   Optional representative citizen records age by one year, update employment
   and housing status, and append a story line describing how the turn affected
   them.

11. Report

   The turn produces a `YearResult`: updated state, revenue, expenses,
   population delta, jobs delta, housing gap, active issues, and overcome
   issues. The updated state also tracks city metrics such as happiness, crime,
   growth rate, labor force, resident employment, unemployment, job vacancies,
   commuters, housing pressure, density, and service coverage.

## Internal Turn Resolution

The current game turn is one year. Inside that year, the simulator may evaluate
representative sub-periods such as winter, spring, summer, fall, weekday peaks,
weekends, nighttime operations, school terms, event seasons, or emergency
periods. These internal periods are not player-visible turns yet; they are a
way to preserve timing and seasonality while keeping annual scenario comparison
simple.

Seasonal climate should be modeled this way. For example, a severe summer heat
profile can increase air-conditioning demand, stress the electric grid, create
brownouts, increase heat illness among seniors or other vulnerable groups,
raise EMS and hospital load, damage public trust, and increase political unrest.
The annual result should report the causal chain rather than only showing a
generic decline in satisfaction.

Some systems also need feedback. A simple one-pass sequence such as
`climate -> grid -> health -> unrest` can miss knock-on effects where later
layers affect earlier capacities. For example, unrest may slow emergency
operations, stress staffing, disrupt communication, or delay cooling-center and
grid response, which then worsens unresolved heat exposure.

To handle this without switching to hourly simulation, an annual turn can use
bounded feedback passes:

```text
annual turn
  build outside, policy, seasonal, and schedule pressures
  evaluate representative periods
  run causal layers once
  feed selected feedback signals into dependent layers
  repeat until stable or until a small fixed pass limit is reached
  commit the yearly state and report the causal chain
```

Feedback signals should be named intermediate values, not hidden side effects.
Examples include grid shortfall, blackout hours, healthcare surge, excess
deaths, civic trust loss, unrest pressure, emergency response delay, staffing
disruption, business interruption, service backlog, and communication failure.
The current source implementation exposes these in-turn intermediates through a
`PressureLedger` on `YearResult`. The first implemented slice derives a severe
summer heat cascade from heat exposure, cooling demand, grid shortfall,
healthcare surge, and civic trust risk.
Signals that should persist beyond the current turn can become
`DelayedEffect` records on `CityState.pending_effects`. A delayed effect stores
its source, target channel, amount, delay, duration, decay, tags, and
explanation. This is the carry-forward layer for impacts that mature over
several turns, such as trust damage after blackouts, infrastructure repair
backlogs, legal-aid backlog, chronic health load, or long-tail business
disruption.

Use delayed effects for intermediate channels, not as shortcuts directly to
final headline metrics. For example:

```text
good: summer_blackout -> civic_trust / healthcare_surge / repair_backlog
bad:  summer_blackout -> happiness -10
```

If the feedback pass does not stabilize, distinguish two cases:

- civic instability: a plausible cascading failure, such as heat, grid
  shortfall, hospital overload, trust collapse, unrest, and delayed response
  reinforcing each other;
- model instability: coefficients or formulas are too sensitive, missing
  damping, or exceeding plausible bounds.

Civic instability should produce active issues, severity, amplifying factors,
missing buffers, and report text. Model instability should produce a warning
for calibration review.

Shorter turns can be added later, such as monthly or quarterly turns, when
mid-year intervention timing becomes important. Shorter turns improve timing
but do not remove the need for feedback modeling: even a monthly turn can
contain daily or hourly crisis dynamics. Keep the feedback machinery explicit
and keep annual scenario reports as a supported output.

## UrbanSim-Inspired Benchmark Goal

UrbanSim's examples organize a regional simulation around canonical tables,
computed columns, named model steps, and fixed workflows. The useful benchmark
for City Simulator is not to copy UrbanSim's full econometric or GIS stack, but
to keep the same separation of concerns:

- canonical state stores source facts;
- views bundle related aggregate statistics derived from lower-level models;
- named turn steps update or derive one part of the city at a time;
- step order is explicit because later steps depend on earlier outputs;
- reports consume step outputs and views rather than recomputing hidden logic.

UrbanSim is deeper than City Simulator currently is for parcel/building-level
real estate, household and job location choice, prices/rents, development
feasibility, and developer behavior. City Simulator is aiming at broader civic
coverage: crisis cascades, public sentiment, public safety, services,
partnerships, institutions, delayed effects, and mayor-style scenario
briefings. Treat UrbanSim as the benchmark for the land-use and real-estate
engine, not as the full scope of the game.

For real estate-style work, the eventual sequence should resemble:

```text
prices/rents view
  household and business demand
  development feasibility
  developer/project pipeline
  updated buildings or neighborhood market state
  refreshed affordability, vacancy, displacement, and scenario comparison views
```

The current `ANNUAL_TURN_STEPS` registry is the first small move toward that
pattern while preserving the annual turn and deterministic CLI behavior.

## Design Rules

- Keep turns deterministic by default.
- Keep phase effects traceable to policy or outside pressure.
- Prefer adding named intermediate values over hiding behavior in one large
  expression.
- Preserve feedback loops explicitly. When one layer can affect an earlier
  capacity or a later layer through a knock-on effect, pass a named feedback
  signal through bounded internal passes instead of assuming a single yearly
  ordering captures the whole chain.
- Carry delayed state explicitly. When an effect should mature later or persist
  across turns, store it as a delayed effect with source, target, timing,
  decay, tags, and explanation.
- Mark variables by provenance:
  - source state / canonical state: authoritative simulated facts;
  - scenario input, policy control, and external pressure: values supplied to a
    run;
  - model parameter: tunable formula coefficient;
  - computed intermediate: temporary value inside a turn;
  - derived rollup: value recomputed from lower-level state;
  - cached metric: derived value stored for reporting or compatibility;
  - report-only output: value emitted in a `YearResult`.
- Treat hard-coded formula weights as scaffolding. As mechanics stabilize,
  promote important weights into named model parameters; when appropriate, let
  those parameters become dynamic city traits that change across turns in
  response to policy, institutions, infrastructure, market conditions, and
  population composition.
- Model the whole city first, but keep the data model neighborhood-ready.
  Neighborhoods are the next useful spatial unit for housing, services, safety,
  job access, civic assets, and sentiment. Individual city blocks should wait
  until neighborhood-level simulation creates a clear need for that resolution.
- Keep neighborhoods topological until maps are needed. Neighborhood records
  should track size, land-use mix, adjacent neighborhoods, adjacent city
  sectors, connectivity, environmental exposure, service access, housing stock,
  and assistance capacity without requiring coordinates or polygons.
- Use shared place assets for physical or institutional locations that can host
  services. A place asset can represent a school, clinic, hospital, mall,
  mixed-use building, police station, fire station, public works depot, transit
  hub, assisted-living residence, congregation, museum, monument, or historic
  site, bank, federal credit union, lending office, public finance office, or
  exchange-market access institution. Embedded services let one place provide
  several capacities, such as education, healthcare, therapy, retail,
  recreation, exhibitions, visitor services, worship, safety response, public
  works access, household credit, business lending, municipal finance, or
  energy-market access.
- Financial institution profiles should distinguish the institution from the
  market it touches. For example, an energy derivatives exchange can give
  energy suppliers, county distributors, large energy consumers such as
  datacenters, and speculators access to power, natural-gas, or environmental
  contracts for price, credit, liquidity, and basis-risk management. The
  simulator should model those participant roles and asset classes without
  treating the exchange as a power plant, physical dispatch system, or generic
  bank.
- Let places and embedded services carry operating schedules. Keep them as
  deterministic annualized profiles for now: business-hours shops, daytime
  weekday school terms, evening adult education, nightlife, overnight public
  works such as street cleaning, seasonal recreation, event-only venues,
  emergency/on-call services, and 24x7 facilities should all be representable
  without simulating every hour.
- Treat housing stock and housing assistance as separate concepts. Physical
  stock includes residence types such as estate homes, rowhouses, mixed-use
  shopfront housing, garden apartments, and high-rises. Assistance includes
  Section 8 vouchers, shelter beds, transitional housing, permanent supportive
  housing, and homelessness prevention capacity.
- Treat redevelopment policies such as pinui-binui as programs that affect
  existing stock, temporary displacement, replacement units, added density,
  construction disruption, political trust, and long-term capacity.
- Treat top-level metrics as derived outputs. As the city and population model
  becomes more detailed, statistics such as population, unemployment, happiness,
  public sentiment, crime, housing pressure, housing stress, and economic
  confidence should be computed from underlying household, cohort, neighborhood,
  business, labor, housing, service, and place data. A starter city or wizard
  may accept initial values such as 100,000 residents or 5% unemployment, but
  after turns begin those values should be derived from simulated lower-level
  data rather than carried forward as manually controlled metrics.
- `city.population` should eventually be a derived rollup/cache from
  household/cohort and neighborhood residency data, not an independently
  authoritative source field.
- `city.metrics.housing_pressure` should be a derived metric from household
  demand, household size, housing supply by type, vacancy, crowding,
  rent/mortgage affordability, assistance utilization, housing condition,
  displacement, and neighborhood distribution.
- When adding a new scenario lever, decide which turn phase it affects.
- When adding a new issue, decide which phase creates or resolves it.
