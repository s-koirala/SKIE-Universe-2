"""Tests for the ADR-0015 verdict-precondition REPORTING check.

Required cases (ADR-0015 / execution brief step 1.3):

- same-hash pair                          -> BLOCKED (distinct_expert_hash_count = 1)
- distinct hashes, identical coverage     -> BLOCKED (no disjoint pair)
- distinct hashes, disjoint coverage      -> MET (reporting only)

Plus: malformed config refusal, empty-coverage exclusion, and the exit-code
contract of ``main``. The checker is a reporting check only — nothing here
wires it into pre-commit or CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.audits.check_verdict_precondition import (
    EXIT_BLOCKED,
    EXIT_ERROR,
    EXIT_MET,
    evaluate_precondition,
    main,
    realized_bar_report_lines,
)

_MIN_REQUIRED = 2  # mirrors the operator instruction registered in the schema block


def _write_schema(tmp_path: Path, min_required: object = _MIN_REQUIRED) -> Path:
    schema = tmp_path / "pool_ledger_schema.yaml"
    schema.write_text(
        "schema_version: 1\n"
        "verdict_precondition:\n"
        "  provisional: true\n"
        "  derivation: operator-directed, NOT calibrated\n"
        f"  min_distinct_disjoint_coverage: {min_required}\n"
        "  enforcement: reporting-check-only\n",
        encoding="utf-8",
    )
    return schema


def _record(expert_hash: str, cells: list[str]) -> str:
    return json.dumps(
        {
            "provenance": {"expert_hash": expert_hash},
            "competence_structure": {"competence_window_cells": cells},
        }
    )


def _write_ledger(tmp_path: Path, rows: list[str]) -> Path:
    ledger = tmp_path / "pool_ledger.jsonl"
    ledger.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return ledger


def test_same_hash_pair_blocked(tmp_path: Path) -> None:
    """Two records sharing one expert_hash -> BLOCKED on the distinct-hash count."""
    ledger = _write_ledger(
        tmp_path,
        [
            _record("orb_first_hour_k1.0@1.0.0", ["ES:first_hour_up"]),
            _record("orb_first_hour_k1.0@1.0.0", ["NQ:non_stress"]),
        ],
    )
    result = evaluate_precondition(ledger, _write_schema(tmp_path))
    assert result.status == "BLOCKED"
    assert result.reason == "distinct_expert_hash_count = 1"
    assert result.distinct_expert_hash_count == 1


def test_distinct_hashes_identical_coverage_blocked(tmp_path: Path) -> None:
    """Two implementations covering the same cells -> BLOCKED (no disjoint pair)."""
    cells = ["ES:first_hour_up", "NQ:high_vol"]
    ledger = _write_ledger(
        tmp_path,
        [_record("expert_a@1.0.0", cells), _record("expert_b@1.0.0", cells)],
    )
    result = evaluate_precondition(ledger, _write_schema(tmp_path))
    assert result.status == "BLOCKED"
    assert "disjoint" in result.reason
    assert result.distinct_expert_hash_count == _MIN_REQUIRED


def test_distinct_hashes_disjoint_met(tmp_path: Path) -> None:
    """Two implementations with non-overlapping coverage vectors -> MET."""
    ledger = _write_ledger(
        tmp_path,
        [
            _record("expert_a@1.0.0", ["ES:first_hour_up", "NQ:high_vol"]),
            _record("expert_b@1.0.0", ["ES:overnight", "NQ:overnight"]),
        ],
    )
    result = evaluate_precondition(ledger, _write_schema(tmp_path))
    assert result.status == "MET"
    assert "operator-gated" in result.reason


def test_partial_overlap_blocked(tmp_path: Path) -> None:
    """A single shared cell breaks disjointness -> BLOCKED."""
    ledger = _write_ledger(
        tmp_path,
        [
            _record("expert_a@1.0.0", ["ES:first_hour_up", "NQ:high_vol"]),
            _record("expert_b@1.0.0", ["NQ:high_vol", "ES:overnight"]),
        ],
    )
    result = evaluate_precondition(ledger, _write_schema(tmp_path))
    assert result.status == "BLOCKED"


def test_empty_coverage_vector_cannot_satisfy(tmp_path: Path) -> None:
    """An empty coverage vector covers nothing and never counts toward MET."""
    ledger = _write_ledger(
        tmp_path,
        [
            _record("expert_a@1.0.0", ["ES:first_hour_up"]),
            _record("expert_b@1.0.0", []),
        ],
    )
    result = evaluate_precondition(ledger, _write_schema(tmp_path))
    assert result.status == "BLOCKED"
    assert "non-empty" in result.reason


def test_coverage_unions_across_records_of_one_hash(tmp_path: Path) -> None:
    """Coverage is the union over a hash's records; overlap via union -> BLOCKED."""
    ledger = _write_ledger(
        tmp_path,
        [
            _record("expert_a@1.0.0", ["ES:first_hour_up"]),
            _record("expert_a@1.0.0", ["NQ:overnight"]),
            _record("expert_b@1.0.0", ["NQ:overnight"]),
        ],
    )
    result = evaluate_precondition(ledger, _write_schema(tmp_path))
    assert result.status == "BLOCKED"


def test_malformed_min_required_refused(tmp_path: Path) -> None:
    """A malformed operator instruction is an error, not a silent default."""
    ledger = _write_ledger(tmp_path, [_record("expert_a@1.0.0", ["ES:x"])])
    with pytest.raises(ValueError, match="min_distinct_disjoint_coverage"):
        evaluate_precondition(ledger, _write_schema(tmp_path, min_required=1))


def test_missing_competence_structure_refused(tmp_path: Path) -> None:
    """Absent competence_window_cells is schema drift -> error, not empty coverage."""
    ledger = tmp_path / "pool_ledger.jsonl"
    ledger.write_text(
        json.dumps({"provenance": {"expert_hash": "expert_a@1.0.0"}}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="competence_window_cells"):
        evaluate_precondition(ledger, _write_schema(tmp_path))


def test_missing_block_refused(tmp_path: Path) -> None:
    """A schema without the verdict_precondition block is an error."""
    schema = tmp_path / "schema.yaml"
    schema.write_text("schema_version: 1\n", encoding="utf-8")
    ledger = _write_ledger(tmp_path, [_record("expert_a@1.0.0", ["ES:x"])])
    with pytest.raises(ValueError, match="verdict_precondition"):
        evaluate_precondition(ledger, schema)


def test_main_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() maps MET/BLOCKED/error to the documented exit codes."""
    schema = _write_schema(tmp_path)

    blocked = _write_ledger(tmp_path, [_record("a@1", ["ES:x"]), _record("a@1", ["ES:y"])])
    monkeypatch.setattr(
        "sys.argv",
        ["check", "--pool-ledger", str(blocked), "--schema", str(schema)],
    )
    assert main() == EXIT_BLOCKED

    met_ledger = tmp_path / "met.jsonl"
    met_ledger.write_text(
        _record("a@1", ["ES:x"]) + "\n" + _record("b@1", ["NQ:y"]) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["check", "--pool-ledger", str(met_ledger), "--schema", str(schema)],
    )
    assert main() == EXIT_MET

    monkeypatch.setattr(
        "sys.argv",
        ["check", "--pool-ledger", str(tmp_path / "missing.jsonl"), "--schema", str(schema)],
    )
    assert main() == EXIT_ERROR


class TestRealizedBarReport:
    """ADR-0017 D2: the realized-bar basis is reported alongside; the exit
    code stays keyed on the label rule; absence is stated, never substituted."""

    def test_absent_addendum_reports_label_only(self, tmp_path: Path) -> None:
        lines = realized_bar_report_lines(_write_schema(tmp_path))
        assert len(lines) == 1
        assert "no realized_bar_input addendum" in lines[0]

    def test_absent_artifact_states_absence(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config"
        cfg.mkdir()
        schema = cfg / "pool_ledger_schema.yaml"
        schema.write_text(
            "verdict_precondition:\n"
            "  min_distinct_disjoint_coverage: 2\n"
            "  realized_bar_input:\n"
            "    artifact: reports/M1_overlap/m1_realized_overlap.json\n"
            "    machinery: scripts/run_m1_overlap_report.py\n",
            encoding="utf-8",
        )
        lines = realized_bar_report_lines(schema)
        assert len(lines) == 1
        assert "M1 artifact absent" in lines[0]
        assert "No substitute" in lines[0]

    def test_present_artifact_renders_pairs(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config"
        cfg.mkdir()
        schema = cfg / "pool_ledger_schema.yaml"
        schema.write_text(
            "verdict_precondition:\n"
            "  min_distinct_disjoint_coverage: 2\n"
            "  realized_bar_input:\n"
            "    artifact: reports/M1_overlap/m1_realized_overlap.json\n",
            encoding="utf-8",
        )
        art = tmp_path / "reports" / "M1_overlap"
        art.mkdir(parents=True)
        (art / "m1_realized_overlap.json").write_text(
            json.dumps(
                {
                    "pairs": [
                        {
                            "experts": ["a@1", "b@1"],
                            "bar_level_jaccard": 0.0,
                            "session_level_jaccard": 0.5,
                            "pre_scan_prediction": {"bar_level": "EXACTLY 0"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        lines = realized_bar_report_lines(schema)
        assert any("a@1 <-> b@1" in ln and "J_bar=0.0" in ln for ln in lines)
        assert any("exit code keys on the label rule" in ln for ln in lines)


class TestRealizedBarRobustness:
    """CR-1-1/CR-1-3/CR-1-5: no realized-bar reporting failure may reach the
    label-keyed exit code; malformed inputs degrade to plain report lines."""

    def _schema_with_artifact(self, tmp_path: Path) -> Path:
        cfg = tmp_path / "config"
        cfg.mkdir()
        schema = cfg / "pool_ledger_schema.yaml"
        schema.write_text(
            "verdict_precondition:\n"
            "  min_distinct_disjoint_coverage: 2\n"
            "  realized_bar_input:\n"
            "    artifact: reports/M1_overlap/m1_realized_overlap.json\n",
            encoding="utf-8",
        )
        return schema

    def test_corrupt_artifact_degrades_to_line(self, tmp_path: Path) -> None:
        schema = self._schema_with_artifact(tmp_path)
        art = tmp_path / "reports" / "M1_overlap"
        art.mkdir(parents=True)
        (art / "m1_realized_overlap.json").write_text("{not json", encoding="utf-8")
        lines = realized_bar_report_lines(schema)
        assert len(lines) == 1
        assert "unreadable" in lines[0]
        assert "no substitute is reported" in lines[0].lower()

    def test_malformed_experts_entry_degrades(self, tmp_path: Path) -> None:
        schema = self._schema_with_artifact(tmp_path)
        art = tmp_path / "reports" / "M1_overlap"
        art.mkdir(parents=True)
        (art / "m1_realized_overlap.json").write_text(
            json.dumps({"pairs": [{"experts": ["only_one"], "bar_level_jaccard": 0.1}, "junk"]}),
            encoding="utf-8",
        )
        lines = realized_bar_report_lines(schema)
        assert any("only_one <-> ?" in ln for ln in lines)
        assert any("malformed pair entry skipped" in ln for ln in lines)

    def test_main_exit_code_immune_to_corrupt_artifact(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """A MET label verdict must exit 0 even when the M1 artifact is corrupt
        (ADR-0017 D2: the exit code keys on the label rule)."""
        schema = self._schema_with_artifact(tmp_path)
        art = tmp_path / "reports" / "M1_overlap"
        art.mkdir(parents=True)
        (art / "m1_realized_overlap.json").write_text("{corrupt", encoding="utf-8")
        ledger = _write_ledger(
            tmp_path,
            [
                _record("expert_a@1.0.0", ["ES:cell_a"]),
                _record("expert_b@1.0.0", ["NQ:cell_b"]),
            ],
        )
        monkeypatch.setattr(
            "sys.argv",
            ["check", "--pool-ledger", str(ledger), "--schema", str(schema)],
        )
        assert main() == EXIT_MET
        out = capsys.readouterr().out
        assert "MET" in out
        assert "unreadable" in out
