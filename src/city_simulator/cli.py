from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from city_simulator.citizens import advance_citizen_histories, generate_representative_citizens
from city_simulator.model import CityPolicy, CityState, ExternalControls, simulate
from city_simulator.scenario import ScenarioError, load_city, load_scenario, save_city
from city_simulator.starter import STARTER_PRESETS, prompt_for_starter_city, write_starter_city
from city_simulator.storage import city_path, ensure_data_dirs, saved_cities


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="city-simulator",
        description="Run a deterministic statistics-only city simulation.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="run one or more scenarios")
    _add_run_arguments(run_parser)

    play_parser = subparsers.add_parser("play", help="open the turn-based city REPL")
    _add_run_arguments(play_parser)

    init_parser = subparsers.add_parser("init-city", help="write a starter city JSON file")
    init_parser.add_argument("path", help="destination JSON file")
    init_parser.add_argument("--preset", choices=sorted(STARTER_PRESETS), default="balanced")
    init_parser.add_argument("--population", type=float)
    init_parser.add_argument("--wizard", action="store_true", help="ask demographic questions")

    _add_run_arguments(parser)
    return parser


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--years", type=int, default=10, help="number of years to simulate")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--citizen-stories", type=int, default=0)
    parser.add_argument("--city", help="JSON file describing the starting city")
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="JSON scenario file. May be passed more than once for comparison.",
    )
    parser.add_argument("--tax-rate", type=float, default=0.18)
    parser.add_argument("--housing-investment", type=float, default=25_000_000)
    parser.add_argument("--transit-investment", type=float, default=18_000_000)
    parser.add_argument("--services-investment", type=float, default=22_000_000)
    parser.add_argument("--environment-investment", type=float, default=8_000_000)
    parser.add_argument("--business-support", type=float, default=10_000_000)
    parser.add_argument("--citizen-influx-rate", type=float, default=0.006)
    parser.add_argument("--citizen-outflux-rate", type=float, default=0.003)
    parser.add_argument("--zoning-restrictiveness", type=float, default=0.35)
    parser.add_argument("--permitting-speed", type=float, default=0.55)
    parser.add_argument("--development-restriction", type=float, default=0.25)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init-city":
        try:
            if args.wizard:
                city = prompt_for_starter_city()
                ensure_data_dirs()
                destination = city_path(args.path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("w", encoding="utf-8") as handle:
                    json.dump(asdict(city), handle, indent=2)
                    handle.write("\n")
            else:
                city = write_starter_city(args.path, args.preset, args.population)
        except ValueError as exc:
            print(f"city-simulator: {exc}")
            return 2
        print(
            f"Wrote {args.preset} city to {city_path(args.path)} "
            f"with population {city.population:,.0f}"
        )
        return 0

    if args.command == "play":
        return _play(args)

    try:
        city_ref = args.city or _prompt_for_saved_city()
        initial_state = load_city(city_ref) if city_ref else CityState()
        runs = _build_runs(args)
    except ScenarioError as exc:
        print(f"city-simulator: {exc}")
        return 2

    reports = [
        {
            "name": name,
            "years": years,
            "results": simulate(initial_state, policy, years, external),
            "citizens": [],
        }
        for name, policy, external, years in runs
    ]
    if args.citizen_stories:
        for index, report in enumerate(reports):
            citizens = generate_representative_citizens(initial_state, args.citizen_stories, index)
            report["citizens"] = advance_citizen_histories(citizens, report["results"])

    if args.format == "json":
        print(json.dumps(_reports_asdict(reports), indent=2))
        return 0

    if len(reports) == 1:
        print(f"Scenario: {reports[0]['name']}")
        print(_format_table(reports[0]["results"]))
        if reports[0]["citizens"]:
            print()
            print(_format_citizens(reports[0]["citizens"]))
    else:
        print(_format_comparison(reports))
        if any(report["citizens"] for report in reports):
            print()
            print(_format_comparison_citizens(reports))
    return 0


def _play(args: argparse.Namespace, input_func=None, output_func=print) -> int:
    if input_func is None:
        input_func = input
    try:
        city_ref = args.city or _prompt_for_saved_city(input_func, output_func)
        if not city_ref:
            output_func("No saved cities found. Create one with `init-city NAME --wizard`.")
            return 2
        state = load_city(city_ref)
        runs = _build_runs(args)
        if len(runs) != 1:
            output_func("city-simulator: play accepts at most one scenario")
            return 2
        scenario_name, policy, external, _years = runs[0]
    except ScenarioError as exc:
        output_func(f"city-simulator: {exc}")
        return 2

    output_func(f"Continuing {city_ref} with scenario: {scenario_name}")
    output_func(_format_state_status(state))
    while True:
        raw = input_func("city> ").strip()
        if raw in {"quit", "q", "exit"}:
            return 0
        if raw in {"help", "h", "?"}:
            output_func("Commands: status, turn [N], next [N], help, quit")
            continue
        if raw in {"status", "s"}:
            output_func(_format_state_status(state))
            continue
        if raw.startswith("turn") or raw.startswith("next") or raw == "":
            count = _turn_count(raw)
            for _ in range(count):
                result = simulate(state, policy, 1, external)[0]
                state = result.state
                output_func(_format_table([result]))
            saved_path = save_city(city_ref, state)
            output_func(f"Saved {city_ref} to {saved_path}")
            continue
        output_func("Unknown command. Type `help`.")


def _turn_count(raw: str) -> int:
    parts = raw.split()
    if len(parts) == 1 or raw == "":
        return 1
    if len(parts) != 2:
        return 1
    try:
        return max(1, int(parts[1]))
    except ValueError:
        return 1


def _format_state_status(state: CityState) -> str:
    return (
        f"Year {state.year}: population {state.population:,.0f}, "
        f"budget ${state.budget:,.0f}, happiness {state.metrics.happiness:.1f}, "
        f"sentiment {state.metrics.public_sentiment:.1f}, "
        f"unemployment {state.metrics.unemployment_rate:.1%}, "
        f"crime {state.metrics.crime:.1f}, growth {state.metrics.growth_rate:.2%}"
    )


def _prompt_for_saved_city(input_func=None, output_func=print) -> str | None:
    if input_func is None:
        input_func = input
    cities = saved_cities()
    if not cities:
        return None
    output_func("Saved cities:")
    for index, path in enumerate(cities, start=1):
        output_func(f"  {index}. {path.stem}")
    raw = input_func("Continue from which city? [1]: ").strip()
    if not raw:
        return cities[0].stem
    try:
        choice = int(raw)
    except ValueError:
        return raw
    if not 1 <= choice <= len(cities):
        raise ScenarioError(f"city choice must be between 1 and {len(cities)}")
    return cities[choice - 1].stem


def _build_runs(args: argparse.Namespace) -> list[tuple[str, CityPolicy, ExternalControls, int]]:
    if args.scenario:
        runs = []
        for scenario_path in args.scenario:
            name, policy, external, scenario_years = load_scenario(scenario_path)
            runs.append(
                (
                    name,
                    policy,
                    external,
                    scenario_years if scenario_years is not None else args.years,
                )
            )
        return runs

    return [
        (
            "manual policy",
            CityPolicy(
                tax_rate=args.tax_rate,
                housing_investment=args.housing_investment,
                transit_investment=args.transit_investment,
                services_investment=args.services_investment,
                environment_investment=args.environment_investment,
                business_support=args.business_support,
                citizen_influx_rate=args.citizen_influx_rate,
                citizen_outflux_rate=args.citizen_outflux_rate,
                zoning_restrictiveness=args.zoning_restrictiveness,
                permitting_speed=args.permitting_speed,
                development_restriction=args.development_restriction,
            ),
            ExternalControls(),
            args.years,
        )
    ]


def _format_table(results: list[object]) -> str:
    headers = (
        "Year",
        "Population",
        "Children",
        "Working",
        "Seniors",
        "Budget",
        "Happy",
        "Sent",
        "Unemp",
        "Crime",
        "Growth",
        "Issues",
        "Overcome",
    )
    rows = [
        (
            str(result.year),
            f"{result.state.population:,.0f}",
            f"{result.state.demographics.children:,.0f}",
            f"{result.state.demographics.working_age:,.0f}",
            f"{result.state.demographics.seniors:,.0f}",
            f"${result.state.budget:,.0f}",
            f"{result.state.metrics.happiness:.1f}",
            f"{result.state.metrics.public_sentiment:.1f}",
            f"{result.state.metrics.unemployment_rate:.1%}",
            f"{result.state.metrics.crime:.1f}",
            f"{result.state.metrics.growth_rate:.2%}",
            _issue_names(result.active_issues),
            _issue_names(result.overcome_issues),
        )
        for result in results
    ]
    widths = [
        max(len(header), *(len(row[index]) for row in rows)) if rows else len(header)
        for index, header in enumerate(headers)
    ]
    lines = ["  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))]
    lines.extend(
        "  ".join(value.rjust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(lines)


def _issue_names(issues: list[object]) -> str:
    if not issues:
        return "none"
    return ", ".join(issue.name for issue in issues)


def _format_comparison(reports: list[dict[str, object]]) -> str:
    headers = (
        "Scenario",
        "Years",
        "Population",
        "Budget",
        "Happy",
        "Sent",
        "Unemp",
        "Crime",
        "Growth",
        "Issues",
        "Overcome",
    )
    rows = []
    for report in reports:
        results = report["results"]
        final = results[-1] if results else None
        overcome = _all_overcome_issue_names(results)
        rows.append(
            (
                str(report["name"]),
                str(report["years"]),
                f"{final.state.population:,.0f}" if final else "n/a",
                f"${final.state.budget:,.0f}" if final else "n/a",
                f"{final.state.metrics.happiness:.1f}" if final else "n/a",
                f"{final.state.metrics.public_sentiment:.1f}" if final else "n/a",
                f"{final.state.metrics.unemployment_rate:.1%}" if final else "n/a",
                f"{final.state.metrics.crime:.1f}" if final else "n/a",
                f"{final.state.metrics.growth_rate:.2%}" if final else "n/a",
                _issue_names(final.active_issues) if final else "none",
                ", ".join(overcome) if overcome else "none",
            )
        )
    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    lines = ["  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))]
    lines.extend(
        "  ".join(value.rjust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(lines)


def _all_overcome_issue_names(results: list[object]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for result in results:
        for issue in result.overcome_issues:
            if issue.code not in seen:
                seen.add(issue.code)
                names.append(issue.name)
    return names


def _reports_asdict(reports: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "name": report["name"],
            "years": report["years"],
            "results": [asdict(result) for result in report["results"]],
            "citizens": [asdict(citizen) for citizen in report["citizens"]],
        }
        for report in reports
    ]


def _format_citizens(citizens: list[object]) -> str:
    lines = ["Citizen Stories"]
    for citizen in citizens:
        lines.append(
            f"- {citizen.id}: age {citizen.age}, {citizen.income_group} income, "
            f"satisfaction {citizen.satisfaction:.1f}"
        )
        lines.append(f"  {citizen.history[-1]}")
    return "\n".join(lines)


def _format_comparison_citizens(reports: list[dict[str, object]]) -> str:
    lines = ["Citizen Story Samples"]
    for report in reports:
        citizens = report["citizens"]
        if not citizens:
            continue
        lines.append(f"{report['name']}:")
        for citizen in citizens:
            lines.append(f"- {citizen.id}: {citizen.history[-1]}")
    return "\n".join(lines)
