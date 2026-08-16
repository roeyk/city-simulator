# City Simulator Goals

Last updated: 2026-08-15

## Project Thesis

City Simulator models a city under pressure. The core workflow is:

1. Define a starting city.
2. Throw one or more scenarios at it.
3. Run the simulation for N iterations.
4. Compare what happened.

A scenario is not only a local city policy package. It can also include policies
and pressures imposed from outside the city, such as county funding, state
mandates, federal support, interest rates, growth pressure, or national
unemployment pressure.

The simulator should answer:

- who lives in the city now;
- whether people moved in or left;
- which civic, financial, market, and infrastructure institutions exist;
- which policies attracted or deterred population;
- what issues emerged;
- what issues were overcome;
- which tradeoffs came from city choices versus outside pressure.

## Primary Experience

The first complete experience is a command-line comparison tool. A user should
be able to run several scenarios against the same starting city and see how
population, demographics, budget, housing, jobs, pollution, satisfaction, and
issues diverge.

The output should feel like a mayoral briefing backed by transparent numbers,
not a graphics-first game and not a raw spreadsheet dump.

## Project Positioning

City Simulator is intended to sit between two kinds of systems:

- compact AI settlement/crisis benchmarks such as Pocket Providence-style
  experiments, where a model makes constrained decisions over a short crisis and
  is judged on survival, resource tradeoffs, ethics, and postmortem reasoning;
- professional urban analysis systems such as UrbanSim or geospatial settlement
  tooling, where policy scenarios, land use, households, jobs, infrastructure,
  and regional pressures are analyzed with more formal data and planning
  workflows.

This project should be more systemic than a toy crisis benchmark, but more
inspectable and gameplay-oriented than a professional planning model. It should
support annual mayor-scale scenario comparison, while eventually allowing
smaller compact crisis benchmarks to test emergency decision-making, resource
triage, ethics, and causal reasoning.

## Scenario Model

Scenarios should support multiple levels of control:

- City policies: taxes, housing investment, services, transit, environment,
  business support, migration incentives, zoning restrictiveness, permitting
  speed, and development restrictions.
- County controls: funding and housing directives.
- State controls: funding, service mandates, and environmental mandates.
- Country controls: federal funding, population growth pressure, interest
  rates, and national unemployment pressure.
- Market and financial context: credit availability, municipal finance access,
  bond-market exposure, energy-market access, commodity exposure, lender
  presence, and institutional liquidity or risk where those systems are modeled.

This structure lets the project test questions such as:

- What if the city cuts taxes but reduces services?
- What if zoning restrictions deter new residents?
- What if permitting reform makes housing investment more effective?
- What if county housing directives offset local restrictions?
- What if state environmental mandates improve satisfaction but change the
  budget picture?
- What if national unemployment pressure overwhelms local business incentives?

## Simulation Goals

- Deterministic by default: the same city and scenario inputs produce the same
  outputs.
- Scenario-first: model changes should make it easier to compare possible
  futures.
- Explainable: major outcomes should be traceable to city policy or outside
  pressure.
- Outcome-aware: active issues and overcome issues are first-class outputs.
- Tunable: policy effects, thresholds, and formulas should be easy to adjust as
  the intended feel becomes clearer.

## World Assumptions

- Owner/design decision: people in this city do not eat animals. Food demand,
  restaurants, groceries, supply chains, and employment should not require
  animal meat, slaughter, butcheries, or meat-processing establishments.
- Animal-related systems should focus on companion animals, service animals,
  animal care, shelters/rescues, adoption, zoos, sanctuaries, wildlife
  rehabilitation, conservation, and public health.

## Near-Term Milestones

1. Stabilize the city and scenario JSON format.
2. Add a city starter system for creating new baseline city files.
3. Stabilize and document the yearly turn model.
4. Improve comparison output so it shows final outcomes and main causes.
5. Add issue histories with causes, interventions, and resolution notes.
6. Expand representative citizen stories toward richer personal histories that
   can explain how city-level changes affect individual residents.
7. Add more scenario examples for high-tax services, low-tax growth, restrictive
   zoning, permissive zoning, austerity, and outside-mandate stress.
8. Add report output that summarizes why people moved in or left.

## Non-Goals For Now

- No graphical interface until scenario comparison is useful on its own.
- No real-time simulation loop.
- No hidden randomness in baseline runs.
- No claim of real-world policy accuracy; the model should be plausible,
  transparent, and tunable.
