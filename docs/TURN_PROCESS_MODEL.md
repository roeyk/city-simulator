# Turn Process Model

Last updated: 2026-08-18

This document describes how new city domains should join the annual turn
without making the simulator monolithic.

For the current source step order, see [`TURN_MODEL.md`](TURN_MODEL.md).

## Goal

Every major domain concept should declare:

- what need it serves;
- what source state it owns or reads;
- what derived views it provides;
- what signals it registers;
- what turn step consumes those signals or views;
- what outputs it changes;
- what tests prove the behavior.

This keeps the model explainable as the simulator grows into supply chains,
regional flows, hospitality, civic groups, faith profiles, relationship
networks, infrastructure, and more detailed organizations.

## Domain Extension Sequence

Use this sequence when adding a new domain:

1. Define the domain need.
2. Add source state or domain records.
3. Add derived views for rollups.
4. Add signal concepts.
5. Add or extend turn steps.
6. Feed outputs into metrics, issues, delayed effects, or reports.
7. Add focused validation.

Do not start by directly changing headline metrics if a named intermediate can
explain the path.

## 1. Define The Need

A domain should have a concrete simulation need, not just a data wish.

Examples:

- Supply chains need to explain stockouts, imports, prices, and service
  failures.
- Commutes need to explain job access, outbound/inbound traffic, pollution,
  cost burden, and stress.
- Hospitality needs to explain visitor nights, event surges, room occupancy,
  restaurant spending, sanitation load, and traffic.
- Cultural belonging needs to explain access, trust, bridge capacity, and
  institutional relationships without deterministic assumptions about identity.

The need should be short enough to fit into a `SignalConcept.need` field when
the domain emits turn signals.

## 2. Add Source State Or Domain Records

Canonical state stores source facts. It should not store every derived answer.

Examples:

- `SupplyNode`
- `SupplyGood`
- `SupplyContract`
- `InventoryState`
- `LogisticsRoute`
- `SectorMarketBalance`
- `IntercityFlow`
- `RegionalTradeFlow`
- `VisitorFlow`
- `HospitalityVenueProfile`
- `OrganizationMembership`
- `FaithProfile`

Prefer separate relationship and flow records when a person or organization can
participate in many relationships. Do not force every relationship into
`PersonAgent` or `OrganizationAgent`.

## 3. Add Derived Views

Views compute rollups from source state and agents. They should be deterministic
and testable outside the annual turn.

Examples:

- `SupplyChainBalanceView`
- `SectorMarketBalanceView`
- `CommuteFlowView`
- `RegionalFlowView`
- `HospitalityDemandView`
- `LanguageAccessView`
- `CulturalBelongingView`

Views are the right place for calculations such as:

- local demand versus local production;
- import dependency;
- stockout risk;
- commute shares;
- visitor nights;
- room occupancy;
- service access;
- bridge capacity;
- sector utilization.

## 4. Add Signal Concepts

Signals are named turn intermediates. They can represent pressures, needs,
flows, capacities, balances, risks, buffers, service gaps, unmet demand, or
import dependencies.

Each `SignalConcept` must declare:

- `name`
- `need`
- `inputs`
- `outputs`
- `channels`
- `collect`

Example shape:

```python
SignalConcept(
    name="supply_chain_balance",
    need="Expose goods and service shortages before they affect prices, service quality, or issues.",
    inputs=("state.supply_nodes", "state.supply_contracts", "state.organizations"),
    outputs=("SignalLedger",),
    channels=(
        "fresh_food_import_gap",
        "supplier_concentration_risk",
        "freight_route_bottleneck",
    ),
    collect=add_supply_chain_signals,
)
```

Signal collectors should call `SignalLedger.add(...)`. They should not directly
mutate `CityState`.

## 5. Add Or Extend Turn Steps

Add a turn step when a domain changes state or produces intermediates that
later steps must consume.

Use `TurnStep.requires` and `TurnStep.produces` to make dependencies visible.
Tests should assert that each step's requirements are already produced by an
earlier step.

Examples:

- Supply chain may need a step before sentiment and issue detection.
- Commute flow may need a step after jobs but before pollution and sentiment.
- Hospitality/event load may need a step before traffic, sanitation, public
  safety, and revenue.
- Regional flows may need a step before labor market, supply chains, and
  visitor demand.

If a domain only exposes reportable intermediates, a signal concept may be
enough for the first slice.

## 6. Feed Outputs Carefully

A domain output can feed:

- `CityMetrics`;
- `Issue` detection;
- `DelayedEffect`;
- CLI/report text;
- saved city state;
- downstream views;
- later turn steps.

Prefer this path:

```text
source state -> view -> signal -> downstream turn step -> metric/issue/report
```

Avoid this path:

```text
scenario flag -> final metric
```

For example, a fresh-food disruption should first create import gaps,
inventory drawdown, route bottlenecks, price pressure, or unmet demand. Later
steps can translate those signals into household cost burden, food insecurity,
business stress, public sentiment, or active issues.

## 7. Validate The Domain

Validation should scale with risk.

For a narrow domain signal slice:

- focused view tests;
- focused signal collection tests;
- focused turn tests proving headline behavior is preserved or changed
  intentionally;
- `ruff check`;
- pyright when typed surfaces changed.

For parser/state changes:

- scenario parsing tests;
- save/load round-trip tests;
- compatibility tests for omitted fields.

For cross-domain flows:

- origin/destination reconciliation tests;
- conservation/balance tests;
- disruption propagation tests;
- representative CLI run.

## Flow Consistency Rules

Flows should reconcile across sources and destinations.

Supply:

```text
local demand - local production - starting inventory - confirmed imports + exports
= shortage_or_surplus
```

Labor:

```text
resident workers - suitable local jobs - remote jobs
= local unmatched workers
```

Unmatched workers can become unemployed, relocate, work remotely for outside
employers, or commute to nearby cities. Nearby-city work should produce
outbound trips unless remote.

Intercity movement:

```text
origin outflow = destination inflow
```

When the destination city is not modeled in detail, represent it as an external
regional node with capacity, demand, reliability, cost, and travel burden.

## Modularity Rules

- Keep ledgers generic.
- Let domains own their own signal names and formulas.
- Centralize only shared driver category constants and orchestration.
- Keep relationship records separate from agent records when relationships can
  be many-to-many.
- Keep views deterministic and side-effect free.
- Keep turn steps ordered and dependency-declared.
- Keep reports consuming named intermediates rather than recomputing hidden
  logic.

## Current Baseline

Current active signal concepts:

- `seasonal_heat_cascade`
- `language_service_access`
- `sector_market_balance`

Current annual turn steps:

```text
validate_inputs
local_fiscal_policy
development_and_jobs
infrastructure_environment
seasonal_signals
satisfaction_migration_demographics
labor_market
sentiment
commit_state
detect_issues
```

This is the baseline to extend. New domains should make their state, views,
signals, step dependencies, and validation explicit.
