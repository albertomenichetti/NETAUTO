# M4 WIP — Object RENAME approximate lifecycle semantics

Status: SUPERSEDED DISCOVERY CHECKPOINT / M4 WIP / NON-NORMATIVE GLOBALLY

## Supersession

Every earlier lifecycle candidate in this file is superseded.

Current ratified Object.RENAME direction is owned by:

```text
to-be-api-object-rename.md
```

The final current direction is neither:

```text
approximate complete intrinsic snapshots
```

nor:

```text
exact complete intrinsic snapshots
```

Instead RENAME records the **exact minimal semantic transition it owns**:

```text
canonical_name: old -> new
```

Conceptually:

```text
RENAME event
    object_id = O
    before.canonical_name = exact old name
    after.canonical_name  = requested/new name
```

Unchanged Object state is not duplicated merely to make the event look like another intrinsic mutation family:

```text
template_id       not part of RENAME transition
template_version  not part of RENAME transition
properties        not part of RENAME transition
ownership         not part of RENAME transition
Relationships     not part of RENAME transition
```

This follows the ratified M4 lifecycle principle:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

not automatically
    = complete aggregate before + after snapshots
```

The historical transition remains exact; only irrelevant unchanged state is omitted.

The Object current-name mutation and its RENAME lifecycle event still commit or rollback atomically.

Exact PostgreSQL statement fusion, current-name protection and lock mode remain architecture work.

This file remains only as traceability for superseded optimization/snapshot hypotheses and must not be used as current semantic authority.