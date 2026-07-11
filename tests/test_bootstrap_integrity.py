"""Bootstrap-integrity smoke tests.

Verifies that a fresh clone matches the repo's own declared layout:
every subdir named in manifest.json exists, the founding ADRs referenced
by CLAUDE.md are present, and pyproject.toml parses. Expectations are
read from the manifests themselves — no hand-maintained lists.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _manifest() -> dict:
    return json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))


def test_manifest_subdirs_exist():
    missing = [d for d in _manifest()["subdirs"] if not (REPO_ROOT / d).is_dir()]
    assert not missing, f"manifest.json subdirs absent from checkout: {missing}"


def test_founding_adrs_present():
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"docs/decisions/(ADR-\d{4}-[\w-]+\.md)", claude_md))
    assert linked, "CLAUDE.md links no ADRs — reference extraction broken"
    missing = [f for f in sorted(linked) if not (REPO_ROOT / "docs" / "decisions" / f).is_file()]
    assert not missing, f"ADRs linked in CLAUDE.md but absent: {missing}"
    empty = [
        f for f in sorted(linked) if (REPO_ROOT / "docs" / "decisions" / f).stat().st_size == 0
    ]
    assert not empty, f"ADR files present but empty: {empty}"


def test_pyproject_parses_and_is_non_package():
    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        cfg = tomllib.load(fh)
    assert cfg["project"]["name"]
    # An empty [build-system] table is schema-invalid and breaks `uv sync`;
    # this repo is intentionally non-installable (tool.uv.package = false).
    assert "build-system" not in cfg or cfg["build-system"].get("requires")
    assert cfg.get("tool", {}).get("uv", {}).get("package") is False


def test_data_manifest_exists_and_parses():
    manifest_path = REPO_ROOT / "data" / "_manifest.json"
    assert manifest_path.is_file(), "data/_manifest.json missing (reproducibility contract)"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "files" in payload


def test_precommit_config_has_no_machine_local_paths():
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    for hook_line in config.splitlines():
        if hook_line.strip().startswith("entry:"):
            assert not re.search(
                r"[A-Za-z]:[/\\]Users[/\\]", hook_line
            ), f"machine-local absolute path in pre-commit entry: {hook_line.strip()}"
