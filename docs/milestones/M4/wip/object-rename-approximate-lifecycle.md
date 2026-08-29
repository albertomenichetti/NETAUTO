# M4 WIP — Object RENAME approximate lifecycle semantics

Status: SUPERSEDED DISCOVERY CHECKPOINT / M4 WIP / NON-NORMATIVE GLOBALLY

## Supersession

The approximate-lifecycle candidate recorded by the earlier version of this file is **superseded**.

Current ratified Object.RENAME direction is owned by:

```text
to-be-api-object-rename.md
```

and requires exact complete intrinsic lifecycle snapshots for the Object generation actually renamed.

The earlier candidate allowed an unlocked preliminary Object snapshot to become stale relative to a concurrent intrinsic mutation before the canonical-name UPDATE. That would permit a RENAME lifecycle event whose `before_state` / `after_state` did not describe the exact Object generation on which the rename was performed.

That relaxation is no longer accepted.

Current requirement:

```text
RENAME.before
    = exact complete intrinsic Object state immediately before the rename transition

RENAME.after
    = exact complete intrinsic Object state immediately after the rename transition

only semantic difference
    = canonical_name
```

The Object current-state transition and RENAME lifecycle event remain atomic.

Exact PostgreSQL statement fusion, lock mode and old/new-row carrier are deferred to architecture. RENAME is not expected to be sufficiently frequent to justify weakening historical correctness solely to save bounded synchronization work.

This file remains only as traceability for the superseded optimization hypothesis and must not be used as current semantic authority.
