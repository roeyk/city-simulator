# Turn Model

Last updated: 2026-08-15

City Simulator advances in yearly turns. A turn should be understandable as a
sequence of civic changes, not a black-box formula.

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
   and state environmental mandates reduce pollution.

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
   with the previous year's issues to identify what was overcome.

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

## Design Rules

- Keep turns deterministic by default.
- Keep phase effects traceable to policy or outside pressure.
- Prefer adding named intermediate values over hiding behavior in one large
  expression.
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
  hub, assisted-living residence, or congregation. Embedded services let one
  place provide several capacities, such as education, healthcare, therapy,
  retail, recreation, worship, safety response, or public works access.
- Treat housing stock and housing assistance as separate concepts. Physical
  stock includes residence types such as estate homes, rowhouses, mixed-use
  shopfront housing, garden apartments, and high-rises. Assistance includes
  Section 8 vouchers, shelter beds, transitional housing, permanent supportive
  housing, and homelessness prevention capacity.
- Treat redevelopment policies such as pinui-binui as programs that affect
  existing stock, temporary displacement, replacement units, added density,
  construction disruption, political trust, and long-term capacity.
- Treat top-level metrics as derived outputs. As the city and population model
  becomes more detailed, statistics such as unemployment, happiness, public
  sentiment, crime, housing stress, and economic confidence should be computed
  from underlying household, business, labor, housing, service, and place data.
  A starter city or wizard may accept an initial value such as 5% unemployment,
  but after turns begin that value should be derived from the simulated city and
  population data rather than carried forward as a manually controlled metric.
- When adding a new scenario lever, decide which turn phase it affects.
- When adding a new issue, decide which phase creates or resolves it.
