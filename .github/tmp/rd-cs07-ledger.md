
## CS-07 — committed property-history linearization — RESOLVED

The owner now distinguishes same-target publication arbitration from Definition-level committed-history arbitration.

```text
PUBLISH same exact DRAFT
    -> target generation/lifecycle gate

PUBLISH different exact DRAFTs of the same Definition
    -> committed-history linearization
    -> incompatible candidates cannot both commit
```

Every successful publication must be compatible with all `PUBLISHED | DEPRECATED` same-name declarations linearized before its commit, under the current datatype-lineage-only continuity rule.

REVISE remains provisional with respect to future history growth: it validates against history at its own commit boundary, but a later publication may make that DRAFT no longer publishable. PUBLISH does not scan or protect unrelated DRAFT candidates and always re-certifies its selected candidate.

`PUBLISHED -> DEPRECATED` does not remove history membership, while DELETE_DRAFT has no history effect. The implementation direction remains set-based early/final probes without worker-side full-history loading or a new history-summary materialization. Exact Definition-local concurrency realization remains architecture work.
