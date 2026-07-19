"""Tests for the VERDICT-1 disposition emitter's append machinery.

Exercises the text-append functions against synthetic repo trees (injected
``ProjectPaths(root=tmp_path)`` per the paths contract): the register-trials
anchor logic (first conversion, subsequent anchor append, layout-drift
refusal, idempotence), the adjudication-index parser, the arsenal
create/append/skip flow, and the incumbent-set hash determinism. No verdict
statistic is computed here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _load_emitter():
    if "emit_verdict_disposition" in sys.modules:
        return sys.modules["emit_verdict_disposition"]
    spec = importlib.util.spec_from_file_location(
        "emit_verdict_disposition", _ROOT / "scripts" / "emit_verdict_disposition.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["emit_verdict_disposition"] = mod
    spec.loader.exec_module(mod)
    return mod


from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

_E = _load_emitter()

_FAMILY_BLOCK = (
    "families:\n"
    "  - family_id: first-admission-verdict\n"
    "    correction: romano-wolf\n"
    "    prds_argument_ref: null\n"
    "    measured_dependence: null\n" + _E._EMPTY_TRIALS_LINE + "\n"
    '    registered_at: "2026-07-19"\n'
)


_COLUMNS = [f"{s}:k{f}" for s in ("ES", "NQ") for f in _E.KELLY_GRID]  # 8 columns


def _result(m_prime: int = 1, admitted: bool = False) -> dict:
    col_sharpes = [0.1 * (j + 1) for j in range(len(_COLUMNS))]
    inference = {
        "marginal": {
            "columns": list(_COLUMNS),
            "column_sharpes": col_sharpes,
            "spa_p_consistent": 0.5,
            "stepm_adjusted_p": [1.0] * len(_COLUMNS),
            "stepm_identified": [False] * len(_COLUMNS),
        }
    }
    if m_prime > 1:
        for r in ("b1", "b3", "b4"):
            inference[r] = {"column_sharpes": col_sharpes}
    return {
        "set_size_augmented": m_prime,
        "columns": list(_COLUMNS),
        "inference": inference,
        "rotor_by_column": {ck: {"p_sidak_column_union": 0.9} for ck in _COLUMNS},
        "dsr_by_column": {ck: {"dsr": 0.1} for ck in _COLUMNS},
        "pbo": {"pbo": 0.9, "bound": 0.74},
        "conjunction": {
            "admitted": admitted,
            "marginal_spa_pass": False,
            "ladder_iu_spa_max_p": 0.5,
            "ladder_iu_pass": False,
            "rotor_min_sidak_p": 0.9,
            "qualifying_columns": [],
            "best_qualifying_column_reported_not_selected": None,
            "persistence_pass": False,
        },
        "incumbents_at_adjudication": [],
        "screen_level_runtime": 0.74,
        "current_trial_surface": 16 if m_prime == 1 else 40,
        "n_trials_cumulative": 56,
        "seed": 20260721,
        "n_bootstrap": 1000,
        "n_rotors": 2000,
        "repro_log": "repro_log_x.json",
        "protocol": "research/02_verdict/VERDICT-1_protocol.md",
        "protocol_sha256": "ab" * 32,
        "disposition": (
            "admitted-arsenal-member" if admitted else "pool-hold-reconsider (re-affirmed)"
        ),
        "degenerate_rungs": ["b1", "b3"],
        "identity_anchor_b2": "EW(U) is the §1 set functional",
    }


def _paths(tmp_path: Path) -> ProjectPaths:
    p = ProjectPaths(root=tmp_path)
    p.config.mkdir()
    (p.config / "multipletest_family.yaml").write_text(_FAMILY_BLOCK, encoding="utf-8")
    return p


class TestAdjudicationIndex:
    def test_first_is_one(self) -> None:
        assert _E._adjudication_index(_FAMILY_BLOCK, "H106") == 1

    def test_next_after_existing(self) -> None:
        text = _FAMILY_BLOCK + "      - hid: VERDICT:H106:A3:ES:k1.0:rotor\n"
        assert _E._adjudication_index(text, "H106") == 4

    def test_stems_do_not_collide(self) -> None:
        text = _FAMILY_BLOCK + "      - hid: VERDICT:H101+H103:A2:NQ:k1.0:rotor\n"
        assert _E._adjudication_index(text, "H106") == 1
        assert _E._adjudication_index(text, "H101+H103") == 3


class TestRegisterTrialsAppend:
    def test_first_append_converts_empty_line(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        n = _E.append_register_trials(p, "H106", _result(), 1, "2026-07-19", "reports/x.json")
        text = (p.config / "multipletest_family.yaml").read_text(encoding="utf-8")
        assert n == 16  # |U| = 1 surface: (marginal-flat + rotor) x 8 columns
        assert _E._EMPTY_TRIALS_LINE not in text
        assert _E._ANCHOR in text
        assert text.count("- hid: VERDICT:H106:A1:") == 16
        # instrument carried in the id keeps ES/NQ column-trials distinct
        assert text.count("- hid: VERDICT:H106:A1:ES:") == 8
        assert text.count("- hid: VERDICT:H106:A1:NQ:") == 8
        assert 'registered_at: "2026-07-19"' in text

    def test_second_adjudication_appends_at_anchor(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        _E.append_register_trials(p, "H106", _result(), 1, "2026-07-19", "reports/x.json")
        n = _E.append_register_trials(
            p, "H105", _result(m_prime=2), 1, "2026-07-20", "reports/y.json"
        )
        text = (p.config / "multipletest_family.yaml").read_text(encoding="utf-8")
        assert n == 40  # |U| >= 2 surface: (marginal + b1 + b3 + b4 + rotor) x 8
        assert text.count("- hid: VERDICT:H106:A1:") == 16
        assert text.count("- hid: VERDICT:H105:A1:") == 40
        assert text.count(_E._ANCHOR) == 1
        # H105 block sits before the anchor, after the H106 block.
        assert (
            text.index("VERDICT:H106:A1") < text.index("VERDICT:H105:A1") < text.index(_E._ANCHOR)
        )

    def test_idempotent_per_index(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        _E.append_register_trials(p, "H106", _result(), 1, "2026-07-19", "reports/x.json")
        n = _E.append_register_trials(p, "H106", _result(), 1, "2026-07-19", "reports/x.json")
        assert n == 0

    def test_layout_drift_refused(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        (p.config / "multipletest_family.yaml").write_text(
            "families:\n  - family_id: first-admission-verdict\n    trials: []\n",
            encoding="utf-8",
        )
        try:
            _E.append_register_trials(p, "H106", _result(), 1, "2026-07-19", "reports/x.json")
        except RuntimeError as e:
            assert "refusing to guess" in str(e)
        else:
            raise AssertionError("layout drift must raise, not guess an insertion point")


class TestArsenalAppend:
    def test_not_admitted_no_file(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        assert _E.append_arsenal(p, "H106", _result(admitted=False), 1, "2026-07-19") is False
        assert not (p.config / "arsenal.yaml").is_file()

    def test_admitted_creates_then_appends(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        assert _E.append_arsenal(p, "H106", _result(admitted=True), 1, "2026-07-19") is True
        text = (p.config / "arsenal.yaml").read_text(encoding="utf-8")
        assert "- candidate: H106" in text
        assert "kelly_fraction_selected: null" in text
        assert _E.append_arsenal(p, "H105", _result(admitted=True), 1, "2026-07-20") is True
        text = (p.config / "arsenal.yaml").read_text(encoding="utf-8")
        assert "- candidate: H106" in text and "- candidate: H105" in text
        assert text.count("members:") == 1

    def test_duplicate_admission_skipped(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        _E.append_arsenal(p, "H106", _result(admitted=True), 1, "2026-07-19")
        assert _E.append_arsenal(p, "H106", _result(admitted=True), 2, "2026-07-20") is False


class TestPoolCopyForward:
    def _seed_ledger(self, p: ProjectPaths, hid: str) -> None:
        # Real records key `hid` at TOP LEVEL (schema record_key); provenance
        # carries expert_hash, not hid — the shape the emitter must read.
        (p.data_processed / "pool_ledger").mkdir(parents=True)
        recs = [
            {
                "hid": hid,
                "kelly_fraction": f,
                "expert_version": "v1",
                "ledger_slice": "ES+NQ:full",
                "provenance": {"expert_hash": f"vr_range_reversal_k{f}@1.0.0"},
                "disposition": {"value": "pool-hold-reconsider"},
            }
            for f in _E.KELLY_GRID
        ]
        (p.data_processed / "pool_ledger" / "pool_ledger.jsonl").write_text(
            "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8"
        )

    def test_copy_forward_keys_top_level_hid(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        self._seed_ledger(p, "H106")
        cards = {
            "H106": p.root / "research" / "01_hypothesis_register" / "H106" / "expert_card_v2.md"
        }
        n = _E.append_pool_records(p, "H106", _result(), 1, "2026-07-19", cards)
        assert n == 4  # one copy-forward per Kelly fraction
        lines = [
            json.loads(x)
            for x in (p.data_processed / "pool_ledger" / "pool_ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if x.strip()
        ]
        assert len(lines) == 8  # 4 original + 4 appended
        appended = lines[4:]
        assert all(r["disposition"]["value"] == "pool-hold-reconsider" for r in appended)
        assert all(r["disposition"]["reconsider_on_set_change"] for r in appended)
        assert all(r["disposition"]["adjudication"]["adjudication_index"] == 1 for r in appended)

    def test_missing_record_raises(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        self._seed_ledger(p, "H105")  # ledger has H105, not H106
        cards = {"H106": p.root / "x" / "expert_card_v2.md"}
        try:
            _E.append_pool_records(p, "H106", _result(), 1, "2026-07-19", cards)
        except RuntimeError as e:
            assert "no pool record to copy forward" in str(e)
        else:
            raise AssertionError("must raise when the candidate has no pool records")


class TestGradeLabeling:
    def test_grade_note_per_candidate(self) -> None:
        # Protocol §7: H105 conditional-grade, H106 net-not-monetizable, ORB standard.
        assert "CONDITIONAL-GRADE" in _E._grade_note("H105")
        assert "net-not-monetizable" in _E._grade_note("H106")
        assert "Tier-0" in _E._grade_note("ORB")

    def test_pool_record_carries_grade_and_cost_label(self, tmp_path: Path) -> None:
        p = _paths(tmp_path)
        # minimal pool ledger with H105 records
        (p.data_processed / "pool_ledger").mkdir(parents=True)
        recs = [
            {
                "hid": "H105",
                "kelly_fraction": f,
                "provenance": {"expert_hash": f"overnight_session_drift_k{f}@1.0.0"},
                "disposition": {"value": "pool-hold-reconsider"},
            }
            for f in _E.KELLY_GRID
        ]
        (p.data_processed / "pool_ledger" / "pool_ledger.jsonl").write_text(
            "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8"
        )
        cards = {"H105": p.root / "r" / "expert_card_v2.md"}
        _E.append_pool_records(p, "H105", _result(), 1, "2026-07-19", cards)
        appended = [
            json.loads(x)
            for x in (p.data_processed / "pool_ledger" / "pool_ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if x.strip()
        ][4:]
        assert all("CONDITIONAL-GRADE" in r["disposition"]["substrate_grade"] for r in appended)
        assert all("Tier-0" in r["disposition"]["cost_label"] for r in appended)


class TestHashAndFormat:
    def test_incumbent_hash_order_invariant(self) -> None:
        assert _E._incumbent_set_hash(["H106", "H105"]) == _E._incumbent_set_hash(["H105", "H106"])
        assert _E._incumbent_set_hash([]) != _E._incumbent_set_hash(["H106"])

    def test_fmt_sr_nan_and_none(self) -> None:
        assert _E._fmt_sr(None) == "null"
        assert _E._fmt_sr(float("nan")) == "null"
        assert _E._fmt_sr(0.123456789) == "0.123457"
