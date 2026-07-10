---
# Expert Card — machine-readable frontmatter (schema per ADR-0009 §3)
hid: <<HID>>
card_version: <<N>>
predecessor_card: <<PATH_OR_NULL>>
design_md_sha256: <<SHA256>>
repro_log_run_ids: [<<RUN_ID_1>>, <<RUN_ID_2>>]
data_span: { start: <<YYYY-MM-DD>>, end: <<YYYY-MM-DD>> }
instruments: [<<SYM_1>>, <<SYM_2>>]
execution_tier: <<0|1|2>>            # per ADR-0006
trial_register_increment: <<INT>>     # scans added to config/multipletest_family.yaml
disposition: <<deploy-candidate|arsenal-admit-conditional|arsenal-admit-diversifier|re-specify-cost-bound|re-specify-execution-bound|archive-no-gross-edge>>
---

# Expert Card — <<HID>> v<<N>>: <<SHORT_TITLE>>

## 1. Provenance header

| Field | Value |
|---|---|
| HID | <<HID>> |
| design.md SHA-256 | <<SHA256>> |
| ReproLog run_id(s) | <<RUN_IDS>> |
| Data span | <<START>> → <<END>> |
| Instruments | <<INSTRUMENTS>> |
| Execution tier | <<TIER>> (ADR-0006) |
| Shadow-ledger partitions | <<PARTITION_REFS>> |
| Trial-register increment | <<INT>> |

## 2. Failure-mode decomposition

| Quantity | Value | CI | Method |
|---|---|---|---|
| Gross (pre-cost) edge | <<VAL>> | <<CI>> | <<METHOD>> |
| Net (post-cost) edge | <<VAL>> | <<CI>> | <<METHOD>> |
| Cost share of gross | <<PCT>> | — | bar-level cost model <<VERSION>> |
| Fold-stability (across-window edge s.d. / mean) | <<VAL>> | — | rolling windows per ADR-0004 |

Classification (exactly one primary; binding numbers stated):
`<<no-gross-edge | cost-bound | fold-unstable | conditional-only | execution-bound>>`
— <<ONE_SENTENCE_BINDING_EVIDENCE>>

## 3. Conditional-edge panel

Conditioning set frozen in design.md §<<N>> on <<DATE>> (pre-scan, ADR-0002 (b)).
Correction: <<Romano-Wolf | Benjamini-Hochberg (PRDS documented) | Benjamini-Yekutieli>> registered in
[config/multipletest_family.yaml](../../config/multipletest_family.yaml).

```yaml
conditional_edges:
  - cell: <<COVARIATE=BUCKET>>
    gross_edge: <<VAL>>
    ci_lower: <<VAL>>
    ci_upper: <<VAL>>
    corrected_significant: <<true|false>>
```

| Conditioning cell | Gross edge | Corrected CI | Significant |
|---|---|---|---|
| <<CELL>> | <<VAL>> | <<CI>> | <<Y/N>> |

## 4. Ensemble block

Arsenal snapshot: <<ARSENAL_MANIFEST_REF>> (<<N>> members at card time).

```yaml
ensemble:
  marginal_ir_estimate: <<VAL>>
  residual_correlation_bound: <<VAL>>   # derived per ADR-0002 (d); derivation memo linked below
  correlations:
    - vs: <<EXPERT_ID>>
      net_residual_corr: <<VAL>>
```

Derivation memo for the correlation bound: <<MEMO_LINK>>

## 5. Stability profile

- Rolling-window edge series: <<FIGURE_OR_TABLE_REF>> (window/cadence per ADR-0004 memo)
- Change-points (CUSUM / BOCPD): <<DATES_OR_NONE>>
- Estimated edge half-life: <<VAL_OR_NA>> (report only if decay detected; method stated)
- Decayed vs never-worked determination: <<ONE_SENTENCE>>

## 6. Disposition

```yaml
disposition: <<TAXONOMY_VALUE>>
binding_criterion: "<<THE_NUMERIC_CRITERION_THAT_BOUND>>"
```

<<2-4 sentences: which criterion bound, at what value, and what would change
the disposition. "pass"/"fail" prohibited per ADR-0009 §2.6.>>

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| <<START>> → <<END>> | <<admission-scan | rolling-eval | confirmation>> | <<COMMIT_SHA>> |

## 8. Priors update

(≤ 5 lines, structured; consumed by queued hypothesis design.)

1. <<CONSTRAINT_STATEMENT>>
2. <<CONSTRAINT_STATEMENT>>
