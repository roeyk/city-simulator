from __future__ import annotations

import json

from city_simulator.code_metrics import analyze_paths, format_table, main


def test_analyze_paths_reports_complexity_coupling_and_cohesion(tmp_path):
    package = tmp_path / "src" / "sample"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "helpers.py").write_text(
        """
def helper(value):
    return value + 1
        """,
        encoding="utf-8",
    )
    (package / "core.py").write_text(
        """
from sample.helpers import helper


class Counter:
    def __init__(self):
        self.value = 0

    def add(self, amount):
        self.value += helper(amount)


def classify(value):
    if value > 10 and value < 20:
        return "middle"
    if value >= 20:
        return "high"
    return "low"
        """,
        encoding="utf-8",
    )

    metrics = {item.module: item for item in analyze_paths([tmp_path / "src"])}

    assert metrics["sample.core"].max_complexity == 4
    assert metrics["sample.core"].cohesion == 1.0
    assert metrics["sample.core"].efferent_coupling == 1
    assert metrics["sample.helpers"].afferent_coupling == 1
    assert metrics["sample.core"].instability == 1.0
    assert metrics["sample.helpers"].instability == 0.0


def test_format_table_includes_metric_columns(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("def ok():\n    return True\n", encoding="utf-8")

    table = format_table(analyze_paths([module]))

    assert "AvgCx" in table
    assert "Coh" in table
    assert "Ce" in table
    assert "Ca" in table
    assert "module" in table


def test_main_can_emit_json(tmp_path, capsys):
    module = tmp_path / "module.py"
    module.write_text("def ok():\n    return True\n", encoding="utf-8")

    assert main([str(module), "--format", "json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output[0]["module"].endswith("module")
    assert output[0]["average_complexity"] == 1.0
