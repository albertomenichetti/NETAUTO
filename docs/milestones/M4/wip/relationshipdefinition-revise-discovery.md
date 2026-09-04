# RelationshipDefinition REVISE — M4 discovery

Status: **TECHNICAL DISCOVERY CLOSED EXCEPT CONCURRENCY/PHYSICAL REALIZATION / WIP / NON-NORMATIVE**

This note is operation-specific source/evidence subordinate to `relationshipdefinition.md` and to the current RelationshipDefinition technical-consolidation ledger.

## Current M4 semantic boundary

`REVISE` is a complete replacement of one exact DRAFT RelationshipDefinitionVersion property schema.

The target must remain:

```text
status = DRAFT
revision = expected_revision
```

Every successful REVISE consumes exactly one DRAFT generation:

```text
revision = expected_revision + 1
```

including when the complete canonical replacement is identical to the current DRAFT candidate.

## Preparation boundary

REVISE starts from the current exact DRAFT snapshot:

```text
status
revision
complete ordered properties
```

Outside the short mutation UoW:

```text
complete request properties[]
    -> resolve every exact DTV pin
       explicit datatype_version
       OR current DataType.default_version
    -> once an omitted default resolves to D@V,
       later default movement does not retarget the in-flight candidate
    -> classify unchanged vs new/changed exact bindings
    -> perform an early set-based historical lineage-continuity probe where useful
    -> load + compile ALL selected exact DTV semantic payloads
    -> validate the complete replacement candidate
```

All selected exact DTVs are loaded/compiled, including unchanged pins.

Lifecycle admission differs by binding class:

```text
unchanged exact pin
    -> semantic load/compile YES
    -> current PUBLISHED requirement NO

new property / changed exact pin
    -> semantic load/compile YES
    -> current PUBLISHED requirement YES
```

Omitted `datatype_version` is always a fresh default-selection instruction, not shorthand for preserving a current exact pin.

## Historical continuity — current M4 revalidated rule

Across all committed `PUBLISHED` / `DEPRECATED` RelationshipDefinitionVersion history, same-name property continuity requires only stable DataType lineage:

```text
same property name
    -> datatype_id MUST remain stable

exact datatype_version
    -> may change

value_mode
    -> SCALAR -> LIST allowed
    -> LIST -> SCALAR allowed
```

The former monotonic rule:

```text
once LIST
    -> later SCALAR forbidden
```

is superseded and is not part of the current M4 RelationshipDefinition model-plane contract.

Reason:

```text
validity of an exact RDV
    !=
ability of every existing factual Relationship to migrate to it
```

Concrete factual `Relationship.SCHEMA_CHANGE` owns preserve-or-fail compatibility for the selected source/target fact. A multi-item LIST may therefore block one concrete migration to a SCALAR target without making that target RDV intrinsically invalid.

## Historical probe direction

Do not materialize the complete committed history in the worker.

For candidate property names, the remaining history violation is conceptually:

```text
historical.name == candidate.name
AND historical.datatype_id != candidate.datatype_id
```

A set-based query may stop at one violating witness.

An early fail-fast probe is useful before expensive compilation, but commit legality must still be re-admitted at the final mutation boundary because another DRAFT of the same Definition may publish while preparation is in progress and add committed history.

Exact concurrency realization remains architecture work.

## Persistence delta

The application already owns both:

```text
current DRAFT snapshot
prepared complete replacement
```

so persistence must not reread property rows merely to compute the delta.

Classify by property name:

```text
unchanged
removed
added
changed
```

where changed includes exact DTV pin, `value_mode`, or internal ordinal differences.

Preferred bounded DML direction:

```text
<= 1 bulk DELETE for removed + changed
<= 1 bulk INSERT for added + changed
1 RDV revision UPDATE
```

Delete-before-insert supports ordinal swaps and uniqueness-sensitive replacement.

If the complete candidate is identical:

```text
property DELETE = 0
property INSERT = 0
revision still increments exactly once
```

No response-only reload is required for the `204 No Content` success contract.

## Final logical admission

```text
1. target-generation gate
       exact RDV exists
       status == DRAFT
       revision == expected_revision

2. dependency admission
       every new/changed exact DTV pin remains PUBLISHED through commit

3. historical admission
       same-name datatype_id continuity remains valid against all
       committed PUBLISHED/DEPRECATED history through commit

4. persist property delta

5. commit exactly the prepared candidate as expected_revision + 1
```

The exact CAS/row-lock/rendezvous sequence remains architecture work.

## Cache/materialization boundary

REVISE does not publish an immutable RDV cache entry because the target remains DRAFT.

No `relationship_definition_space` maintenance occurs because property-schema editing does not change stable Definition topology/name semantic-cell ownership.

No new relational denormalization is justified by REVISE.
