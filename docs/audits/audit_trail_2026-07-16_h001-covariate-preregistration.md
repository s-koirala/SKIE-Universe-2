# Audit trail — H001 conditioning-covariate pre-registration

**Deliverable:** [research/01_hypothesis_register/H001/design.md](../../research/01_hypothesis_register/H001/design.md)
— pre-registration design for hypothesis **H001**, reframing the exploration-tier
SMA(3)/StdDev(3) "meta-shift" prototype from a standalone directional scalping
strategy into an ADR-0001-D5 conditioning covariate whose ADR-0002(d)
non-redundancy vs the registered H900 HMM covariate and the project-standard
variance-ratio state is tested on forward reversion/continuation structure.

**Mechanism:** [audit-remediate-loop](../../../.claude/skills/audit-remediate-loop)
via the Workflow engine ([~/.claude/workflows/audit-remediate.js](../../../.claude/workflows/audit-remediate.js)),
one round per invocation, 3-round cap. Routed branches (deterministic from `.md`
extension + flags): **quant-auditor**, **literature-check**, **format-auditor**.
Every critical/major finding passed an adversarial refute gate before remediation.

**Outcome:** ACCEPT at round 3 (all three branches accept; zero surviving
findings; 3-round cap reached). Runs: round 1 `wf_65227aa0-749`, round 2
`wf_f6542c2f-6a8`, round 3 `wf_1ce6fcb9-5f9`.

## Round 1 — verdict: block (5 remediate, 0 refuted, 9 minors)

| ID | Sev | Branch | Issue | Disposition |
|---|---|---|---|---|
| QUANT-1-1 / LITERATURE-1-1 | critical / major | quant / lit | LeBaron 1992 DOI `10.1086/296583` resolves to Grossman 1992 (unrelated microstructure paper) | **Fixed** — → `10.1086/296565` in frontmatter + §1 mechanism + §1 primary-cites |
| QUANT-1-2 | major | quant | Forward `VR_h(t)=Var(r_{t→t+h})/(h·Var(r_5m))` degenerate (variance of one draw); Lo-MacKinlay attribution imprecise | **Fixed** — §4 redefined as self-normalizing within-window realized VR proxy `(Σr)²/(h·RV_h)`, bounded `[0,h]`, `E≈1` under RW; disclaimed as NOT full-sample Lo-MacKinlay; signal in `E[VR_h∣S]` |
| QUANT-1-3 | major | quant | `h=6` justified as "H900 dwell range" but §3 dwell is 9–12; `h=6` below NQ floor | **Fixed** — `h=12` within-dwell primary; `h=6` relabeled explicit sub-dwell probe; wording corrected |
| FORMAT-1-1 | major | format | `alpha 0.05` lacks `# justify:` | **Fixed** — tagged as descriptive-CI-only; binding FWER is the deferred `screening_error_rate_target` OUTPUT |
| QUANT-1-4 | minor | quant | grid `{2,3,4,5,8}` interior spacing (6,7 omitted) unexplained | **Fixed** — spacing rationale added |
| QUANT-1-5 / LITERATURE-1-3 / FORMAT-1-3 | minor | quant/lit/format | Grinold 1989 orphaned in frontmatter | **Fixed** — cited at §5 (marginal-IR analogue of nested delta) |
| QUANT-1-6 | minor | quant | §1 (LeBaron: high-vol→reversion) vs §5 (prototype: low-vol→reversal) direction mismatch | **Fixed** — reconciliation note; direction is an empirical result, not assumed |
| QUANT-1-7 | minor | quant | stationary bootstrap over ~15 window summaries unreliable | **Fixed** — moved to pooled bar-level contribution series |
| LITERATURE-1-2 | minor | lit | adjusted MI misattributed to Hubert-Arabie 1985 | **Fixed** — AMI → Vinh, Epps & Bailey 2010 |
| LITERATURE-1-4 | minor | lit | Politis-Romano 1994 absent from frontmatter inventory | **Fixed** — added |
| FORMAT-1-2 | minor | format | 25% precision constant untagged | **Fixed** — tagged as H900-inherited convention |

## Round 2 — verdict: proceed-with-remediation (2 major, 0 refuted, 3 minors); lit + format ACCEPT

| ID | Sev | Branch | Issue | Disposition |
|---|---|---|---|---|
| QUANT-2-1 | major | quant | Round-1 `2h`-window sensitivity variant leaks: §6 purge fixed at `h` < `2h` | **Fixed** — §6 purge made horizon-aware `max(feature_lookback, forward_window)` (`h` primary, `2h` variant); López de Prado 2018 ch.7 |
| QUANT-2-2 | major | quant | CMI permutation null not stratified; global permutation of `Y` destroys `Y`–`Z` dependence → inflated Type-I | **Fixed** — §5/§8 specify conditional within-`Z`-cell restricted permutation preserving `p(Y∣Z)`; Runge 2018 AISTATS |
| QUANT-2-3 | minor | quant | `VR_h` is `0/0` when forward `RV_h=0` (flat ETH bars); no NaN rule | **Fixed** — a-priori degenerate-window drop rule registered in §4 |
| LITERATURE-2-1 | minor | lit | KAMA "Kaufman 2013" paired with 6th-ed ISBN (6th ed = 2019/2020) | **Fixed** — → Kaufman 2020 6th ed (ISBN 9781119605355) |
| LITERATURE-2-2 | minor | lit | Tashman 2000, Bergmeir-Benítez 2012, Politis-White 2004, PPW 2009, Hoenig-Heisey 2001 absent from inventory | **Fixed** — five DOIs added to frontmatter |

## Round 3 — verdict: accept (0 findings; all three branches accept; cap reached)

All 18 citations verified to primary sources (tier 1–2), including the two new
method citations (Runge 2018 PMLR v84:938-947; López de Prado 2018 ch.7) and the
five newly-inventoried DOIs. No leakage, method-fidelity, magic-number, or
identity-hygiene issue remains.

## Residual risk (recorded)

- **Deferred FWER-null coherence (quant-auditor round 3, non-blocking):** when the
  deferred `screening_error_rate_target` is instantiated, the Romano-Wolf family-wise
  null must be generated by the same joint within-`Z`-cell restricted permutation as
  the per-arm CMI null (not the bar-level block bootstrap), to keep the family-wise
  conditional null coherent. **Pinned into the frozen design** (§8 "Null coherence
  (registered)"); binds the deferred certification step only, not the descriptive run.
- **Small-window CMI cell sparsity** under the 8-cell conditioning set (`S_hmm`×`S_vr`
  ≥ HMM 4-state × VR 2-state) may be masked rather than resolved by the precision
  gate; monitored at run time via the reported dropped-bar / cell-occupancy counts.
- **Deferred blocks correctly sequenced, not omissions:** the ADR-0002(c)
  conditional-gross-edge scan (shadow-ledger backfill) and any geometric-growth /
  Kelly-fraction ranking (two BLOCKING Decision-9 memos) are out of H001 scope by
  construction; auditors were instructed not to flag them, and did not.
