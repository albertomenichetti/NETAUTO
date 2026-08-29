# M4 WIP — Object SCHEMA_CHANGE bounded retry policy

Status: SUPERSEDED SOURCE MATERIAL / M4 WIP / NON-NORMATIVE GLOBALLY

This note is retained only as historical source material for the earlier fingerprint-era SCHEMA_CHANGE retry design.

Its former current conclusions are superseded by:

- [`object-revision.md`](object-revision.md) for the universal intrinsic Object generation protocol;
- [`object-schema-change.md`](object-schema-change.md) for the revalidated route-specific SCHEMA_CHANGE retry/reprepare semantics.

In particular, the following earlier conclusions are **not current authority**:

```text
protected fingerprint mismatch as stale-generation signal
fixed MAX TOTAL ATTEMPTS = 2 as discovery contract
retry exhaustion -> 409 STATE_CONFLICT
code = schema_change_blocked
blocker_type = concurrent_object_change
```

Current direction is:

```text
expected_revision mismatch
    -> stale intrinsic attempt
    -> no Object/slot/lifecycle mutation
    -> bounded complete fresh retry

exact retry count/backoff
    -> architecture realization detail

bounded retry exhaustion
    -> 500 internal_error
    -> not a normal public 409 business conflict
```

A fresh retry re-reads the current intrinsic Object generation, reuses an immutable MigrationPlan only when the fresh SOURCE identity still matches, resolves a new SOURCE -> TARGET plan when it does not, and returns `204` if the requested exact TARGET has meanwhile become current.

Git history retains the complete earlier fingerprint-specific rationale and examples.