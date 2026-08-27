# M4 WIP — Object.CREATE discovery

**Status:** WIP / NON-NORMATIVE

## Scope

This discovery records the first-phase M4 analysis of the factual `Object.CREATE` hot path. Lock-plan stabilization and cross-operation concurrency proofs remain explicitly deferred to the global concurrency phase.

## Current architectural contract

`Object.CREATE` resolves either an explicit exact ObjectTemplateVersion or the lineage current default, requires the selected exact version to be `PUBLISHED`, requires the lineage to be non-abstract, and validates caller properties against the selected exact version's definitive effective schema. The persisted Object materializes the exact `(template_id, template_version)` pin.

The selected `PUBLISHED` ObjectTemplateVersion is the model-plane consistency anchor. Runtime CREATE must not recursively re-certify or lifecycle-lock every already-certified ancestor/DataType dependency.

## Current hot-path shape

Conceptually the current application path performs:

```text
_selected_template()
    -> load ObjectTemplate lineage
    -> resolve explicit/default version
    -> load exact ObjectTemplateVersion

[lock-plan stabilization; deferred]

_selected_template() again

require selected OTV PUBLISHED
require lineage non-abstract

_runtime_specs()
    -> reload selected exact OTV
    -> rebuild exact parent chain
       -> repeated lineage/version reads
    -> resolve effective schema
    -> load distinct exact DataTypeVersions
    -> recanonicalize persisted DataType constraints
    -> rebuild RuntimePropertySpec objects

canonicalize caller properties
insert Object
insert CREATED lifecycle event
```

## M4 finding — current admission vs immutable semantics

The normal data-plane path should separate current mutable admission from immutable exact schema semantics.

### PostgreSQL remains authority for current admission

CREATE must still establish current facts such as:

```text
ObjectTemplate lineage exists
lineage.abstract == false

explicit selection:
    requested exact version exists

implicit selection:
    current default_version is not NULL
    current default resolves to the selected exact version

selected exact version:
    status == PUBLISHED
```

Cache presence must never prove current existence, current default selection, non-abstract current lineage state, or current PUBLISHED admission.

### Worker-local immutable cache owns runtime semantic payload

For a selected immutable exact version, the data-plane should consume a compiled effective schema cache rather than reconstructing inheritance and DataType semantics per Object.

Candidate shape:

```text
ImmutableObjectTemplateCache[(template_id, version)]
    effective properties:
        declaring_template_id
        name
        exact datatype_id/version pin
        value_mode
        required
        migration_default
        compiled RuntimePropertySpec / validator linkage

    effective components:
        declaring_template_id
        name
        target_template_id
```

The property runtime specs compose immutable ObjectTemplate effective declarations with immutable DataType semantics.

## Strong hot-path eliminations

Independent of final lock design, the following work should disappear from normal cache-hit `Object.CREATE`:

1. the third read of the selected exact ObjectTemplateVersion performed solely by `_runtime_specs()`;
2. exact parent-chain traversal and repeated lineage/version reads;
3. effective-schema reconstruction from local declarations on every Object CREATE;
4. exact DataTypeVersion semantic reloads performed solely to obtain base type / constraints;
5. re-running `canonicalize_constraints()` against already-certified persisted DataType semantics;
6. rebuilding `RuntimePropertySpec` objects for every created Object.

The model-plane `ObjectTemplate.PUBLISH` materialization boundary and the immutable DataType cache should pay these costs once, not every factual CREATE.

## Candidate hot path

With a warm worker cache, the desired conceptual path is:

```text
validate canonical name in memory

PostgreSQL current admission
    -> resolve current explicit/default exact selection
    -> require lineage non-abstract
    -> require selected exact OTV PUBLISHED

lookup ImmutableObjectTemplateCache[(template_id, version)]
    -> compiled effective runtime property specs

canonicalize caller properties in memory

1 INSERT Object
1 INSERT CREATED lifecycle event
COMMIT
```

No recursive exact-parent traversal, DataType constraint reload, or runtime schema recompilation belongs on the normal cache-hit path.

## Non-goals / deferred items

- The duplicate `_selected_template()` reads induced by lock-plan stabilization are not classified here; they remain for the global concurrency phase.
- The exact shape of the cold-cache load is intentionally analyzed separately. A cache miss must not regress to the current parent-chain traversal plus N DataType reads.
- No distributed cache invalidation protocol is introduced. Immutable semantic entries may outlive current existence; PostgreSQL current admission remains authoritative.
