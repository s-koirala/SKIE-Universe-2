---
name: ADR-0011 — Two-level data storage and provenance policy
description: Machine-level raw store outside the repo, project-level processed data materialized by in-project ingest; upstreams registered in config/data_sources.yaml; nothing under data/ committed except manifests and declared exceptions
type: architecture
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
---

# ADR-0011 — Two-level data storage and provenance policy

## Context

SKIE-Universe 1.0 (sibling repo, `C:\Users\skoir\Documents\SKIE-Universe`)
evolved a de-facto two-level layout: vendor raw files live in a
machine-level store outside any repository
(`~/datasets/vendor_skie_ninja_legacy/raw_1min/`, ≈1.7 GB Databento
GLBX.MDP3 ohlcv-1m CSVs covering ES/NQ 2015–2026H1 plus MCL/MGC/SIL), and
each project materializes its own analysis-ready parquet under
`data/processed/` via in-project ingest modules with per-file provenance
records. 2.0 needs the same substrate (the shadow ledger of ADR-0003
backfills from roll-adjusted continuous-contract bars) and must decide
whether to copy 1.0's 373 MB processed parquet, reference it in place, or
re-materialize from raw.

Copying processed parquet across repos duplicates state with no provenance
chain; referencing 1.0's `data/processed/` in place couples 2.0's evidence
to a sibling repo's mutable working tree and violates ADR-0008's
requirement that every evidence artifact carry an in-project checksum.
1.0's own provenance discipline (e.g. the
`es_5min_features_2020_2025.provenance.json` sidecar) already
distinguishes `prototype` from evidence-bar tiers on exactly this ground:
features authored outside the project require in-project re-derivation
before they are evidence-eligible.

## Decision

1. **Two levels, one direction.** Vendor raw data lives in the
   machine-level store `~/datasets/` (outside every repo, never committed,
   backed up independently). Project-level `data/processed/` is
   materialized **only** by in-project ingest code reading from the
   machine-level store (or the vendor API directly). Data flows raw →
   processed; no project writes back into `~/datasets/` except vendor
   retrieval jobs that land new raw files with a provenance sidecar.
2. **No cross-repo processed imports.** 1.0's `data/processed/` parquet is
   not copied into 2.0. The 2.0 evidence-bar substrate is re-materialized
   from the shared raw store by a ported ingest module (Phase C), so every
   evidence artifact's provenance chain terminates at vendor raw files
   registered in this repo.
3. **Upstream registry.** Every external source consumed by this project is
   registered in [config/data_sources.yaml](../../config/data_sources.yaml):
   location, vendor chain, license status, coverage, and (where already
   recorded upstream) checksums. Ingest modules must refuse sources absent
   from the registry.
4. **Checksums at materialization.** Per-file SHA-256 for everything under
   `data/` is recorded in `data/_manifest.json` by
   `scripts/build_data_manifest.py` at ingest time; CI runs `--check` to
   detect drift. Machine-level raw files are checksummed in their
   provenance sidecars at retrieval time, not re-hashed per project run.
5. **Commit policy.** Nothing under `data/` is committed except
   `_manifest.json`, `expectations.yaml`, `.gitkeep` placeholders, and
   explicitly declared exceptions (1.0 precedent: the H055 pilot ledger —
   small, load-bearing, pre-registration artifacts only, each with a
   gitignore exception and a dataset card).
6. **Shadow-ledger placement.** Per ADR-0003, the ledger lives at
   `data/processed/shadow_ledger/` (partition keys `expert_id`, `asset`,
   `session_date`) with per-partition SHA-256 roll-ups in
   `data/_manifest.json`. It is project-level processed data under this
   policy: derived, reproducible from registered upstreams plus expert
   code, never committed.

## Consequences

- Positive: every 2.0 evidence artifact has an unbroken in-repo provenance
  chain to registered vendor raw files; sibling-repo drift cannot silently
  alter 2.0 results.
- Positive: the 1.7 GB raw store is shared across projects without
  duplication; only cheap manifests are committed.
- Negative: Phase C must port and re-run ingest (compute cost) rather than
  copy 373 MB of existing parquet; roll-adjustment logic must be verified
  in-project (PIT canaries per ADR-0008) before the substrate is
  evidence-eligible.
- Obligation: `config/data_sources.yaml` becomes a maintained artifact;
  adding a data source without registering it there is an integrity
  violation under ADR-0008.

## Alternatives considered

- **Copy 1.0's processed parquet into 2.0.** Rejected: duplicates 373 MB
  with a provenance chain terminating in another repo's working tree;
  checksum custody unclear on divergence.
- **Reference 1.0's `data/processed/` in place (path pointer).** Rejected:
  couples evidence to a mutable sibling working tree; 1.0 re-ingests would
  silently change 2.0 results, violating ADR-0003 append-only semantics.
- **Commit the substrate parquet to this repo (LFS/DVC).** Rejected for
  now: adds tooling and hosting cost for data reproducible from the
  registered raw store; revisit only if the raw store's durability becomes
  a concern.

## References

- [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md) — shadow ledger as
  canonical data object (placement, checksum roll-up).
- [ADR-0008](ADR-0008-integrity-non-negotiables.md) — PIT canaries,
  ReproLog, provenance obligations.
- SKIE-Universe 1.0 conventions: `scripts/ingest.py` two-phase commit +
  provenance emission; `data/external/h055_pilot_ledger/` tracked-exception
  precedent;
  `~/datasets/vendor_skie_ninja_legacy/es_5min_features_2020_2025.provenance.json`
  sidecar schema (tier: prototype vs evidence-bar re-derivation
  requirement).
- [config/data_sources.yaml](../../config/data_sources.yaml) — the registry
  this ADR mandates.
