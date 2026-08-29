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

# GP-01 — Version number orders creation, not semantics

For every versioned domain lineage, `version` identifies an **exact version**.

The domain guarantees one generic ordering property:

```text
if exact version VX is created after exact version VY
for the same lineage,
then X > Y
```

Therefore numeric version order is monotonic with exact-version **creation/allocation order inside one lineage**.

This guarantee exists to preserve a simple and intuitive caller-facing rule: creating a new exact version can never produce a number lower than one already allocated for the same lineage.

The guarantee is deliberately narrow.

From version numbers alone it remains invalid to infer:

```text
V2 > V1
    => V2 was generated from V1

V2 > V1
    => V2 is the semantic successor of V1

V2 > V1
    => V2 is semantically wider / more permissive than V1

V2 > V1
    => V1 and V2 are compatible

V2 > V1
    => migration V1 -> V2 is admissible

V2 > V1
    => V2 was published after V1

V2 > V1
    => V2 is current/default/preferred
```

Canonical rule:

```text
version number
    = exact-version identity
    + creation/allocation order within one lineage

version number
    != genealogy
    != semantic evolution order
    != compatibility order
    != migration order
    != publication order
```

A later-created exact version may be derived, cloned or otherwise produced from an older exact version according to the specific operation contract; the version number does not encode that derivation relationship.

The temporal monotonicity guarantee also implies that version numbers are never reused inside one lineage after allocation, even if an exact version is later deleted.

The current cross-domain persistence direction used to realize this guarantee is owned by [`version-allocation.md`](version-allocation.md).

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

# GP-04 — Lifecycle records the operation-owned semantic transition

A lifecycle event must record the complete historical transition that the owning operation is semantically responsible for.

It does **not** follow that every event must duplicate a complete snapshot of the whole aggregate before and after the mutation.

Canonical rule:

```text
lifecycle payload
    = complete exact semantic transition owned by the operation

lifecycle payload
    != automatically
       complete aggregate before snapshot
       + complete aggregate after snapshot
```

Fields and related facts that the operation cannot change do not have to be duplicated merely to make lifecycle payload shapes uniform across mutation kinds.

This avoids turning audit/history representation choices into artificial mutation responsibilities or concurrency dependencies.

For example, `Object.RENAME` owns only:

```text
canonical_name: old -> new
```

and therefore its lifecycle contract can be exact and complete with the old and new canonical-name values, without copying unchanged ObjectTemplate binding, runtime properties, ownership or Relationship state.

By contrast, an operation that creates or destroys a complete current resource may legitimately require a broader snapshot because the whole resource enters or leaves current existence.

The appropriate lifecycle payload boundary must therefore be evaluated operation by operation. Uniform storage or DTO convenience must not silently widen the semantic responsibility of a mutation.

Lifecycle remains historical/audit state; current authoritative state is owned by the current-state persistence model rather than reconstructed implicitly from the event stream unless a separate contract explicitly says otherwise.

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