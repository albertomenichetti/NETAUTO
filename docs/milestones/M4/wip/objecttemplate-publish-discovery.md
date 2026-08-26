# ObjectTemplate.PUBLISH discovery — WIP / NON-NORMATIVE

## Scope

This note records first-phase M4 discovery for `ObjectTemplate.PUBLISH`. It is non-normative. Lock redesign remains deferred to the global concurrency phase.

## AS-IS flow

Current publication roughly does:

1. load ObjectTemplate lineage;
2. load the exact DRAFT aggregate;
3. require DRAFT + expected revision;
4. derive/acquire the current publish dependency lock plan;
5. reload lineage and DRAFT aggregate;
6. require DRAFT + expected revision again;
7. verify lock-plan stability;
8. validate the candidate with history checks;
9. re-read every direct DataType dependency individually and require PUBLISHED;
10. re-read the exact parent ObjectTemplateVersion aggregate and require PUBLISHED;
11. set exact status to PUBLISHED;
12. if lineage default is NULL, set this exact version as default;
13. reload the complete published exact version;
14. commit.

## Publication as certification/materialization boundary

Current preferred M4 direction:

> ObjectTemplate.PUBLISH is the certification + materialization + optional local compilation boundary between mutable model editing and immutable runtime consumption.

The DRAFT effective schema is not maintained as a long-lived materialization. During publication, the final effective schema is built/certified once and then persisted as immutable derived state in the same transaction as the lifecycle transition.

Candidate immutable projections:

```text
object_template_effective_properties
    template_id
    template_version
    name
    position
    declaring_template_id
    datatype_id
    datatype_version
    value_mode
    required
    migration_default

object_template_effective_components
    template_id
    template_version
    name
    position
    declaring_template_id
    target_template_id
```

The semantic authority remains stable lineage + exact parent pin + local declarations. Effective rows are derived/materialized state.

## Reuse the certified EffectiveSchema

Current `_validate_candidate(...)` already computes and returns an `EffectiveSchema`, but PUBLISH ignores the returned object.

M4 should reuse the same certified result for materialization rather than reconstructing the schema again solely for persistence.

Conceptually:

```text
effective = validate/certify candidate

transactional DML:
    persist effective materialization
    status -> PUBLISHED
    optional first default -> this version
```

## Parent materialization reuse

For a non-root DRAFT, its exact parent dependency must be PUBLISHED for publication admission. Therefore the parent exact version is immutable and, under the M4 candidate model, already owns a materialized effective schema.

Candidate derivation:

```text
EffectiveSchema(current DRAFT)
    = EffectiveSchema(exact parent PUBLISHED)
      + current local properties
      + current local components
```

This can avoid traversing/reloading the entire exact ancestor chain during publication. It also reduces the apparent need for a separately materialized exact-version ancestry closure.

## Historical evolution checks remain necessary at publication

A DRAFT being valid at REVISE time is not sufficient to skip history checks at PUBLISH time. Another DRAFT of the same lineage may have been published since the last revision, changing the latest immutable declaration for a property/slot name.

Therefore publication must still certify historical continuity against the latest immutable declarations at publication time.

Preferred data-access direction remains set-based/bulk historical lookup, not per-member N+1 queries and not a new denormalized semantic-history registry.

## Direct dependency admission is current truth

PUBLISH must verify only direct lifecycle-sensitive dependencies:

- exact parent ObjectTemplateVersion, if non-root;
- exact DataTypeVersion pins of local properties.

Inherited DataType dependencies do not need to be re-certified recursively: the exact parent was itself certified when published. Recursive validity follows from direct active-model invariants.

These checks ask current questions (`exists now?`, `status == PUBLISHED now?`) and therefore remain PostgreSQL authority. Immutable caches cannot prove publication admission.

## Data-access finding: set-based/status-oriented dependency checks

AS-IS re-reads DataType dependencies one property at a time, including duplicates when multiple properties share the same exact DataType pin. It also loads the complete exact parent aggregate although only existence/status are needed for this admission check.

Candidate M4 direction:

```text
unique local DataType exact pins
    -> one set-based status projection

exact parent identity, if any
    -> one lightweight header/status projection
```

Do not load immutable semantic payload or full aggregate state merely to answer current lifecycle admission.

Whether these projections can later be absorbed into locking/admission reads is explicitly deferred to the global concurrency redesign.

## Cache population after publication

After successful commit, the exact ObjectTemplateVersion becomes immutable and may populate the worker-local runtime-oriented ObjectTemplate cache.

The cache should be shaped for hot Object operations, not as a byte-for-byte copy of persistence rows. Candidate content includes:

```text
ImmutableObjectTemplateCache[(template_id, version)]
    effective property lookup/runtime specs
    effective component-slot lookup
    declaring-template identities
    exact DataType pins
    compiled/linked DataType validation structures where available
```

No extra PostgreSQL query should be issued only to warm the cache. PUBLISH already has the complete certified effective schema in memory, so local fill is opportunistic after commit; compilation cost remains an implementation/performance policy.

PUBLISHED -> DEPRECATED does not invalidate the immutable semantic cache/materialization.

## Open items

- exact physical DML shape for effective-property/effective-component materialization;
- bulk/set-based historical lookup details;
- lightweight direct-dependency status projections;
- whether local cache compilation should be eager immediately after successful PUBLISH or lazy on first runtime consumer;
- whether PUBLISH response can be constructed from already-held state instead of reloading the complete exact version after DML;
- all lock simplification and concurrency realization questions remain deferred to the second/global phase.
