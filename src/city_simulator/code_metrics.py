from __future__ import annotations

import argparse
import ast
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import TypedDict


@dataclass(frozen=True)
class FunctionMetrics:
    name: str
    complexity: int


@dataclass(frozen=True)
class ModuleMetrics:
    module: str
    path: str
    logical_lines: int
    classes: int
    functions: int
    methods: int
    average_complexity: float
    max_complexity: int
    cohesion: float
    efferent_coupling: int
    afferent_coupling: int
    instability: float
    internal_imports: tuple[str, ...]
    external_imports: tuple[str, ...]


class ModuleSummary(TypedDict):
    logical_lines: int
    classes: int
    functions: int
    methods: int
    average_complexity: float
    max_complexity: int
    cohesion: float
    internal_imports: set[str]
    external_imports: set[str]


def analyze_paths(paths: Iterable[str | Path]) -> list[ModuleMetrics]:
    files = _python_files(paths)
    modules = {_module_name(path): path for path in files}
    summaries = {
        _module_name(path): _analyze_module(path, set(modules))
        for path in files
    }
    afferent: dict[str, set[str]] = {module: set() for module in modules}
    for module, summary in summaries.items():
        for imported in summary["internal_imports"]:
            if imported in afferent and imported != module:
                afferent[imported].add(module)

    metrics: list[ModuleMetrics] = []
    for module in sorted(summaries):
        summary = summaries[module]
        efferent = len(summary["internal_imports"])
        afferent_count = len(afferent[module])
        total_coupling = efferent + afferent_count
        instability = efferent / total_coupling if total_coupling else 0.0
        metrics.append(
            ModuleMetrics(
                module=module,
                path=str(modules[module]),
                logical_lines=summary["logical_lines"],
                classes=summary["classes"],
                functions=summary["functions"],
                methods=summary["methods"],
                average_complexity=round(summary["average_complexity"], 2),
                max_complexity=summary["max_complexity"],
                cohesion=round(summary["cohesion"], 2),
                efferent_coupling=efferent,
                afferent_coupling=afferent_count,
                instability=round(instability, 2),
                internal_imports=tuple(sorted(summary["internal_imports"])),
                external_imports=tuple(sorted(summary["external_imports"])),
            )
        )
    return metrics


def format_table(metrics: list[ModuleMetrics]) -> str:
    headers = (
        "Module",
        "LOC",
        "Cls",
        "Fn",
        "Meth",
        "AvgCx",
        "MaxCx",
        "Coh",
        "Ce",
        "Ca",
        "Inst",
    )
    rows = [
        (
            item.module,
            str(item.logical_lines),
            str(item.classes),
            str(item.functions),
            str(item.methods),
            f"{item.average_complexity:.2f}",
            str(item.max_complexity),
            f"{item.cohesion:.2f}",
            str(item.efferent_coupling),
            str(item.afferent_coupling),
            f"{item.instability:.2f}",
        )
        for item in metrics
    ]
    widths = [
        max(len(row[index]) for row in (headers, *rows))
        for index in range(len(headers))
    ]
    lines = [
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(headers)),
        "  ".join("-" * width for width in widths),
    ]
    lines.extend(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m city_simulator.code_metrics",
        description="Report cohesion, coupling, and complexity metrics for Python code.",
    )
    parser.add_argument("paths", nargs="*", default=["src", "tests"])
    parser.add_argument("--format", choices=["table", "json"], default="table")
    args = parser.parse_args(argv)

    metrics = analyze_paths(args.paths)
    if args.format == "json":
        print(json.dumps([asdict(item) for item in metrics], indent=2))
    else:
        print(format_table(metrics))
    return 0


def _python_files(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if _is_analyzable_python_file(path):
            files.append(path)
        elif path.is_dir():
            files.extend(
                child
                for child in path.rglob("*.py")
                if _is_analyzable_python_file(child)
            )
    return sorted(files)


def _is_analyzable_python_file(path: Path) -> bool:
    return (
        path.suffix == ".py"
        and path.is_file()
        and not path.name.startswith(".")
        and "__pycache__" not in path.parts
    )


def _module_name(path: Path) -> str:
    without_suffix = path.with_suffix("")
    parts = without_suffix.parts
    if "src" in parts:
        module_parts = parts[parts.index("src") + 1 :]
        if module_parts[-1] == "__init__":
            module_parts = module_parts[:-1]
        return ".".join(module_parts)
    if "tests" in parts:
        return ".".join(parts[parts.index("tests") :])
    if without_suffix.name == "__init__":
        return ".".join(without_suffix.parts[:-1])
    return ".".join(without_suffix.parts)


def _analyze_module(path: Path, known_modules: set[str]) -> ModuleSummary:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    function_metrics = [_function_metrics(node) for node in ast.walk(tree) if _is_function(node)]
    class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    complexities = [item.complexity for item in function_metrics]
    internal_imports, external_imports = _imports(tree, known_modules)
    return {
        "logical_lines": _logical_lines(source),
        "classes": len(class_nodes),
        "functions": len(
            [
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            ]
        ),
        "methods": sum(
            1
            for class_node in class_nodes
            for child in class_node.body
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
        ),
        "average_complexity": mean(complexities) if complexities else 0.0,
        "max_complexity": max(complexities, default=0),
        "cohesion": _module_cohesion(class_nodes),
        "internal_imports": internal_imports,
        "external_imports": external_imports,
    }


def _function_metrics(node: ast.AST) -> FunctionMetrics:
    name = getattr(node, "name", "<anonymous>")
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, ast.If | ast.For | ast.AsyncFor | ast.While | ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(len(child.values) - 1, 0)
        elif isinstance(child, ast.IfExp):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += 1 + len(child.ifs)
    return FunctionMetrics(name=name, complexity=complexity)


def _imports(tree: ast.Module, known_modules: set[str]) -> tuple[set[str], set[str]]:
    internal: set[str] = set()
    external: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _record_import(alias.name, known_modules, internal, external)
        elif isinstance(node, ast.ImportFrom) and node.module:
            _record_import(node.module, known_modules, internal, external)
    return internal, external


def _record_import(
    name: str,
    known_modules: set[str],
    internal: set[str],
    external: set[str],
) -> None:
    matched = _known_module(name, known_modules)
    if matched:
        internal.add(matched)
    else:
        external.add(name.split(".", maxsplit=1)[0])


def _known_module(name: str, known_modules: set[str]) -> str | None:
    candidates = [module for module in known_modules if name == module or name.startswith(f"{module}.")]
    if candidates:
        return max(candidates, key=len)
    package = name.split(".", maxsplit=1)[0]
    if package in known_modules:
        return package
    return None


def _module_cohesion(class_nodes: list[ast.ClassDef]) -> float:
    class_scores = [_class_cohesion(node) for node in class_nodes]
    if not class_scores:
        return 1.0
    return mean(class_scores)


def _class_cohesion(node: ast.ClassDef) -> float:
    method_attrs = [
        _self_attributes(child)
        for child in node.body
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    if len(method_attrs) <= 1:
        return 1.0
    total_pairs = 0
    connected_pairs = 0
    for left_index, left_attrs in enumerate(method_attrs):
        for right_attrs in method_attrs[left_index + 1 :]:
            total_pairs += 1
            if left_attrs & right_attrs:
                connected_pairs += 1
    return connected_pairs / total_pairs if total_pairs else 1.0


def _self_attributes(node: ast.AST) -> set[str]:
    attrs: set[str] = set()
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Attribute)
            and isinstance(child.value, ast.Name)
            and child.value.id == "self"
        ):
            attrs.add(child.attr)
    return attrs


def _logical_lines(source: str) -> int:
    return sum(1 for line in source.splitlines() if line.strip() and not line.lstrip().startswith("#"))


def _is_function(node: ast.AST) -> bool:
    return isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)


if __name__ == "__main__":
    raise SystemExit(main())
