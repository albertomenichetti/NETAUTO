# M4 WIP — General domain principles discovered during M4

**Status:** ACTIVE COLLECTION / M4 WIP / ALWAYS NON-NORMATIVE

## Purpose

This file collects **general domain principles** discovered or made explicit during M4 that are not specific to a single route, aggregate or persistence realization.

The intent is to keep these principles in one temporary M4 owner while discovery is still in progress, then promote the validated principles to the appropriate general/normative documentation on `master` during milestone closure.

Until that promotion happens:

```text
this file is WIP
this file is globally non-normative
this file does not authorize implementation
```

Only principles that have been explicitly discussed and ratified during the current discovery should be added here. Route-specific or architecture-specific decisions should remain in their owning documents.

---

# GP-01 — Version number is exact identity, not a global monotonic order

For every versioned domain object, `version` identifies an **exact version**.

The domain does **not** define a global invariant of strict monotonicity between version number and:

```text
creation time
derivation/generation order
semantic evolution
compatibility
migrability
```

Therefore, from version numbers alone, it is invalid to infer any of the following:

```text
V2 > V1
    => V2 was necessarily created after V1

V2 > V1
    => V2 was necessarily generated from V1

V2 > V1
    => V2 is semantically wider / newer / more permissive than V1

V2 > V1
    => migration V1 -> V2 is necessarily admissible

V2 < V1
    => V2 must necessarily predate or be an ancestor of V1
```

In particular, the general domain model does not forbid a version created at a later point in time from having a numerically lower `version` than another version from which, according to the specific operation/history, it may have been derived.

Any stronger ordering rule belongs exclusively to the contract of the specific versioned object or operation that defines it. It must never be inferred as a generic versioning property.

Canonical rule:

```text
version number
    = exact-version identity

version number
    != generic temporal order
    != generic genealogy
    != generic semantic order
    != generic migration order
```

---

# GP-02 — Version validity and cross-version migrability are separate concerns

The validity of one exact version and the migrability between two exact versions are distinct domain concerns.

Canonical separation:

```text
VALIDITY OF VERSION V
    !=
MIGRABILITY FROM VERSION A TO VERSION V
```

An operation that creates, revises, validates or publishes a version must enforce **only the invariants required by the contract of that versioned object and by that operation**.

It must not speculate about whether instances currently bound to another exact version will later be migratable to or from the candidate version, unless such cross-version migrability is explicitly part of that operation's contract.

This applies in particular to operations such as:

```text
REVISE
PUBLISH
```

Their responsibility is to establish that the candidate satisfies the domain contract required for revision/publication. They are not generic migration planners.

---

# GP-03 — REVISE/PUBLISH must not absorb responsibilities of future runtime migrations

For `ObjectTemplate`, `REVISE` and `PUBLISH` must enforce the ObjectTemplate contract, including stable-lineage and exact-version invariants, but must not introduce speculative checks solely to make a future `Object.SCHEMA_CHANGE` succeed.

Example of an invariant that belongs to the ObjectTemplate contract:

```text
stable parent_template_id of an ObjectTemplate lineage
    -> cannot be changed by REVISE
```

Example of a fact that is **not automatically a REVISE/PUBLISH problem**:

```text
version A property p
    -> exact DataTypeVersion DA

version B property p
    -> exact DataTypeVersion DB

DB constraints are not fully compatible with all values valid under DA
```

If the ObjectTemplate/DataType contracts allow the exact dependency selected by version B, `REVISE` or `PUBLISH` must not reject B merely because some runtime Object currently valid under A might fail a future migration to B.

The future migration operation owns that question.

Conceptually:

```text
REVISE / PUBLISH
    -> is this exact version valid according to its own contract?

SCHEMA_CHANGE / other migration operation
    -> can this concrete runtime state move from SOURCE exact version
       to TARGET exact version according to the migration contract?
```

A valid exact version may therefore be:

```text
migratable for every current instance
migratable only for some current instances
not migratable for a particular current instance
```

without that fact alone invalidating the exact version itself.

---

# Promotion note

Before M4 closure, every principle retained here must be reviewed for:

```text
scope
terminology
conflicts with existing normative documentation
correct final owner on master
```

After promotion, this WIP remains historical Git evidence and must not become a competing normative source.