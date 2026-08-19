# City Simulator

City Simulator is a deterministic, statistics-first civic systems simulator.
It is a policy sandbox for defining a city, applying local policies and outside
pressures, advancing time, and comparing how civic systems interact.

The intended experience is a mayoral briefing backed by transparent numbers:
not a graphics-first city builder, and not a raw spreadsheet. The simulator
models causal chains and tradeoffs across population, neighborhoods, housing,
jobs, businesses, services, infrastructure, transportation, environment,
public safety, public sentiment, and city finances.

See [GOALS.md](GOALS.md) for the project thesis: define a city, throw different
policy and outside-pressure scenarios at it, and compare what happens.
See [docs/TURN_MODEL.md](docs/TURN_MODEL.md) for what happens during each
yearly turn and [docs/TURN_PROCESS_MODEL.md](docs/TURN_PROCESS_MODEL.md) for
how new domains should plug into that turn.

The initial model advances one year at a time. Policy settings influence growth,
housing pressure, employment, municipal budget, infrastructure condition,
pollution, resident happiness, crime, growth, and broad demographics. Each year
also reports active city issues and which issues were overcome.
Labor and sentiment metrics are derived from the city state: jobs in the city
are distinct from resident employment, and public sentiment combines survey,
migration, business, spending, savings, housing, safety, services, civic-trust,
and future-confidence signals.

## What We Are Building

City Simulator is becoming a causal urban policy sandbox: a yearly city-change
engine that can explain why outcomes happen, who was affected, and through
which civic systems.

The simulator combines aggregate city systems with enough human, household,
place, and institutional texture to make policies and shocks land unevenly and
explainably. A policy should not directly change a headline metric such as
happiness or population when a more concrete path exists. Instead, effects
should flow through named mechanisms such as rent burden, service access, job
access, language barriers, commute stress, mental-health pressure,
neighborhood exposure, civic trust, business confidence, and delayed risks.

The practical target is a mayoral or controller loop: change policy or face a
scenario, advance the city, and receive a report that explains what changed,
which residents, households, neighborhoods, businesses, and institutions were
affected, which problems emerged or improved, and which risks are building for
future turns.

The interpersonal detail is not an end in itself, but it is an important
reporting surface. The simulator should be able to produce grounded life
stories, household stories, neighborhood stories, and institutional stories
that explain city change at human scale. Those stories should be generated from
access networks, institutions, household conditions, place-based constraints,
and simulated events rather than from flat demographic labels or ungrounded
fiction.

## Where This Project Sits

City Simulator sits between a compact AI crisis benchmark and a professional
urban-planning model.

At the small end, it is inspired by compact settlement-crisis benchmarks:
constrained resources, short crisis horizons, named or representative people,
hard tradeoffs, ethics constraints, and postmortems that test whether an AI
understands the consequences of its decisions.

At the large end, it borrows the scenario-comparison mindset of professional
urban simulation systems: policy levers, households, jobs, development,
infrastructure, regional pressures, path-dependent yearly changes, and
transparent reports.

It is not trying to be a full GIS, econometric land-use forecast, or official
planning model. It is a deterministic civic-systems sandbox for exploring
causal chains: broad enough to model interacting city systems, but small enough
for a person or AI agent to inspect, reason about, and explain.

## Run

```bash
PYTHONPATH=src python3 -m city_simulator --years 5
```

The explicit subcommand form is also supported:

```bash
PYTHONPATH=src python3 -m city_simulator run --years 5
```

Create a starter city:

```bash
PYTHONPATH=src python3 -m city_simulator init-city my-city \
  --preset growing \
  --population 200000
```

Create a starter city with demographic prompts:

```bash
PYTHONPATH=src python3 -m city_simulator init-city my-city --wizard
```

Create a deterministic synthetic test city with generated people, households,
organizations, sector balances, and inventories:

```bash
PYTHONPATH=src python3 -m city_simulator init-city synthetic-test \
  --synthetic \
  --people 30
```

Synthetic cities can also use a JSON group profile to set ethnic/heritage
percentages, group-specific socioeconomic classes, and group-specific vocation
weights:

```json
{
  "groups": [
    {
      "heritage": "anglo",
      "population_share": 50,
      "income_bands": {"middle": 70, "high": 30},
      "job_pools": {"private_service": 60, "business_owner": 40}
    },
    {
      "heritage": "hispanic",
      "population_share": 50,
      "income_bands": {"low": 45, "middle": 55},
      "vocations": {"city_service": 50, "private_service": 50}
    }
  ],
  "mixed_households": [
    {
      "count": 1,
      "members": [
        {"heritage": "american", "income_band": "middle", "age": 42},
        {"heritage": "latino", "income_band": "low", "age": 39},
        {"heritage": "american", "income_band": "middle", "age": 11}
      ],
      "job_pools": {"private_service": 100}
    }
  ]
}
```

```bash
PYTHONPATH=src python3 -m city_simulator init-city profiled-test \
  --synthetic \
  --people 100 \
  --synthetic-profile profile.json
```

Reusable test profiles live in `examples/synthetic-profiles/`. They are
deterministic fixture inputs, not calibrated population estimates. For example:

```bash
PYTHONPATH=src python3 -m city_simulator init-city language-access-test \
  --synthetic \
  --people 120 \
  --synthetic-profile examples/synthetic-profiles/language-access-stress.json
```

Run one scenario against a city:

```bash
PYTHONPATH=src python3 -m city_simulator \
  --city my-city \
  --scenario examples/scenarios/housing-first.json
```

If you omit `--city`, the simulator lists saved cities from
`~/.city-simulator/cities/` and asks which one to continue from.

Open the turn-based REPL:

```bash
PYTHONPATH=src python3 -m city_simulator play --city my-city
```

REPL commands:

- `status`
- `turn` or `next`
- `turn N`
- `help`
- `quit`

Compare several scenarios against the same city:

```bash
PYTHONPATH=src python3 -m city_simulator \
  --city examples/cities/default.json \
  --scenario examples/scenarios/housing-first.json \
  --scenario examples/scenarios/green-transition.json \
  --scenario examples/scenarios/business-growth.json
```

JSON output is available for later tooling:

```bash
PYTHONPATH=src python3 -m city_simulator --years 5 --format json
```

## Policy Knobs

- `--tax-rate`: municipal tax rate, from `0.0` to `1.0`.
- `--housing-investment`: yearly spending on new housing.
- `--transit-investment`: yearly spending on infrastructure.
- `--services-investment`: yearly spending on resident services.
- `--environment-investment`: yearly spending that reduces pollution.
- `--business-support`: yearly spending that improves job growth.
- `--citizen-influx-rate`: baseline yearly migration into the city.
- `--citizen-outflux-rate`: baseline yearly migration out of the city.
- `--zoning-restrictiveness`: `0.0` to `1.0`; higher values suppress housing
  growth and resident satisfaction.
- `--permitting-speed`: `0.0` to `1.0`; higher values make housing investment
  more effective.
- `--development-restriction`: `0.0` to `1.0`; higher values slow job and
  housing growth.

## Output Shape

The table view is a mayor-style annual summary:

- total population;
- age demographics;
- unemployment;
- household income mix;
- active issues;
- issues overcome this year.

When comparing multiple scenarios, the table is followed by a short scenario
briefing. The briefing summarizes population movement, major causal drivers,
turn signals, active issues, and any overcome issues so the comparison
explains why outcomes diverged.

Use JSON output when you want the full state and issue history for a later UI or
scenario comparison.

## City And Scenario Files

City files describe the starting point. Scenario files describe a policy package
to throw at that city. Both are JSON so they can be edited by hand before the
project has a richer interface.

Named cities are stored under:

```text
~/.city-simulator/cities/
```

The starter also creates:

```text
~/.city-simulator/scenarios/
~/.city-simulator/reports/
```

Set `CITY_SIMULATOR_HOME` to use a different data directory.

Starter city presets:

- `balanced`
- `growing`
- `stressed`

The `--wizard` starter asks for population size, age, race, sex, LGB
orientation, nationality, religion, religiosity per religion, education,
literacy by age, school graduation by age cohort, income, workforce category,
and adult family-structure percentages. Adult family structure currently records
values such as married, divorced, second marriage, third-plus marriage, and
adults with children. It also asks for age-by-income splits, so the city can
distinguish young rich populations from older rich populations. It also asks for
physical size in square miles, terrain/coverage mix, developed land share, and
counts for schools, fire stations, police stations, libraries, retail districts,
industrial districts, office districts, government districts, and neighborhoods.
The generated city also includes `cohort_profiles`, a generic place for nested
cohort attributes such as age-by-income, religion-by-religiosity, workforce
class, and future cultural or ethnic cohort breakdowns.

The synthetic city generator is aimed at simulator testing rather than civic
calibration. It produces deterministic people, households, language profiles,
business/community organizations, anchor institutions, sector market balances,
and inventory records so new turn mechanics can be exercised with one city
file.

City files can also include topological neighborhood and housing data. This is
not a map system: neighborhoods are named records with size, land-use mix,
adjacent neighborhoods, adjacent city sectors, connectivity, exposure, service
access, housing stock, and housing assistance. Housing stock can distinguish
estate homes, large-lot single-family homes, rowhouses, mixed-use shopfront
buildings, garden apartments, midrise/high-rise apartments, subsidized units,
senior housing, student housing, and structure-age buckets. Section 8 vouchers,
homeless shelters, transitional housing, permanent supportive housing, and
homelessness prevention are modeled as assistance or service capacity, not as
ordinary housing units.

City and neighborhood files can also include `place_assets`. A place asset is a
topological civic or economic place such as a school, clinic, hospital, mall,
mixed-use building, police station, fire station, public works depot, transit
hub, assisted-living residence, congregation, museum, monument, or historic
site. Place assets can embed `services`, so one building can carry several
usable capacities: for example a school can include daytime education seats,
counseling, a clinic, and recreation programs; a mixed-use building can include
housing-adjacent retail; an assisted living residence can include occupational
therapy; a museum can include exhibitions, school programs, archives, events,
and visitor services. The model tracks capacity, jobs, condition, access,
service area, tags, operating schedule, and per-service
quality/access/trust/schedule without requiring coordinates or map geometry.
Schedules are annualized profiles rather than real-time simulation. They can
describe business hours, daytime school terms, nightlife, overnight public
works such as street cleaning, seasonal services, event-only uses, emergency
on-call coverage, or 24x7 operations.

Financial places can include a `financial_profile`. This lets the same place
model represent banks, federal credit unions, lending institutions, public
finance offices, and exchange-market access institutions. Profiles can track
market roles, participant roles, asset classes, deposit capacity, lending
capacity, municipal finance capacity, household/business access, liquidity, and
risk. For example, an energy exchange market can represent derivatives-market
access for power suppliers such as nuclear or solar generators, county
distributors, large energy consumers such as giga-class datacenters, and
speculators to manage price, credit, liquidity, and basis risk. This is market
risk access, not physical energy dispatch.

City files can include `pending_effects` to carry delayed or persistent impacts
between turns. A delayed effect records a source, target channel, amount,
turn-delay, duration, decay rate, tags, and explanation. This lets a crisis
create lagged effects such as civic-trust damage, healthcare surge,
infrastructure backlog, legal-aid backlog, or business disruption without
pretending every consequence happens in the same turn.

Annual reports can also include a `signal_ledger` with named in-turn signals.
The first implemented signal slice models severe summer heat as
`summer_heat_exposure`, `cooling_demand`, `grid_shortfall`,
`healthcare_surge`, and `civic_trust_risk`. Severe signals can create delayed
effects such as repair backlog, lingering healthcare load, and later civic
trust loss.

Scenario files can include:

- `name`
- `years`
- `policy.tax_rate`
- `policy.business_tax_rate`
- `policy.housing_investment`
- `policy.transit_investment`
- `policy.services_investment`
- `policy.environment_investment`
- `policy.business_support`
- `policy.citizen_influx_rate`
- `policy.citizen_outflux_rate`
- `policy.zoning_restrictiveness`
- `policy.permitting_speed`
- `policy.development_restriction`
- `county.funding`
- `county.housing_directive`
- `state.funding`
- `state.environment_mandate`
- `state.service_mandate`
- `country.funding`
- `country.growth_pressure`
- `country.interest_rate`
- `country.unemployment_pressure`

## Development

```bash
PYTHONPATH=src pytest -q
```

Track code cohesion, coupling, and complexity:

```bash
PYTHONPATH=src python3 -m city_simulator.code_metrics src tests
```

The metrics table reports logical lines, class/function/method counts, average
and maximum cyclomatic complexity, approximate class cohesion, efferent
coupling (`Ce`), afferent coupling (`Ca`), and instability. JSON output is also
available:

```bash
PYTHONPATH=src python3 -m city_simulator.code_metrics src tests --format json
```

This project intentionally starts without persistence, graphics, or randomness.
Those should be added only after the basic turn model and scenario shape are
settled.
