# M4 WIP — ObjectTemplate validation-loader architecture handoff

Status: CROSS-DOMAIN ARCHITECTURE HANDOFF / WIP / NON-NORMATIVE GLOBALLY

## Why this note exists

The route-local TO-BE closure for `Object.CREATE` assumes that, after PostgreSQL has resolved one exact ObjectTemplate binding `(template_id, version)`, the worker can bring the semantic knowledge required for Object validation into cache through an efficient bounded loader.

This capability was already anticipated by the preliminary M4 Object/ObjectTemplate cache findings, but it is not yet physically or normatively defined.

The assumption must not be lost when the top-down sweep later reaches ObjectTemplate.

## Consumer contract already frozen by Object.CREATE

`Object.CREATE` requires the following behavior:

```text
STEP 1
    PostgreSQL resolves exact binding + current PUBLISHED admission

STEP 2
    validation consumes cache only

    cache READY
        -> validate immediately

    cache MISSING or PARTIAL
        -> load/complete immutable/stable semantic knowledge
        -> fill/compile cache
        -> mark validation facet READY
        -> validate from cache
```

CREATE must never fall back to recursive ObjectTemplate/DataType persistence traversal or N+1 exact DataType reads in order to validate one Object candidate.

## Capability that ObjectTemplate architecture must define and norm

When the M4 top-down/architecture work reaches ObjectTemplate, it must explicitly define a reusable capability conceptually equivalent to:

```text
ensure_object_template_validation_ready(template_id, version)
```

The exact software API/name is not frozen here. The required semantics are.

For one exact ObjectTemplateVersion, the capability must make available at least:

```text
stable direct-creation eligibility / abstract semantics
complete effective property schema
    declaring_template_id
    name
    value_mode
    required
    exact datatype_id/version pin

all immutable exact DataTypeVersion semantics referenced by those properties
    stable primitive/base type
    canonical immutable constraints

compiled/runtime validation structures
    RuntimePropertySpec or equivalent
    reusable compiled validator artifacts where beneficial
```

Only a complete READY state is consumable by Object runtime validation.

## Required cold-load properties

The ObjectTemplate phase must decide and norm the physical/materialized read model that makes a cold load efficient.

Target requirements already implied by the Object.CREATE closure:

```text
bounded DB work per exact OTV cold load
no recursive parent-chain reconstruction on the runtime hot/cold path
no per-property / per-DTV N+1 loading
consume M4 effective-schema materialization
bulk-load all semantic knowledge needed for the requested validation facet
opportunistically fill reusable exact DTV cache entries when their payload is already present
```

A cache may be facet-partial. For example, the effective-components facet may already be READY because of `GET Object` while the properties/validation facet is still missing. The loader must complete only the required missing knowledge without forcing unrelated cache facets to be loaded.

## Authority boundary

This loader/cache is not authority for mutable current lifecycle state.

It must not decide:

```text
current default_version
current ObjectTemplateVersion PUBLISHED/DEPRECATED status
current lineage existence as an admission fact
```

Those remain PostgreSQL current-state responsibilities of the consuming command.

Cached exact semantic knowledge may remain valid after `PUBLISHED -> DEPRECATED` because the exact semantic payload is immutable.

## Architecture-phase deliverables

Before M4 architecture can be considered closed, the ObjectTemplate phase must define and norm:

1. the authoritative relational/materialized source for an exact validation-facet cold load;
2. the minimum query/statement shape and bounded-cost expectation;
3. cache facet structure and READY semantics;
4. interaction with the exact DataTypeVersion cache;
5. fill behavior for missing vs partially populated cache entries;
6. concurrency behavior for multiple workers/tasks cold-loading the same exact OTV locally;
7. physical indexes required by the loader, reviewed together with the full ObjectTemplate workload;
8. which model-plane publication/materialization step guarantees that the loader never has to re-certify inheritance/DataType semantics at runtime.

## Dependency classification

This is a cross-domain architecture dependency, not a reason to reopen the already frozen `Object.CREATE` caller/data-path contract.

The Object.CREATE closure remains valid under this explicit assumption:

> M4 ObjectTemplate architecture will provide and norm an efficient reusable way to bring one exact ObjectTemplateVersion validation facet, including its required exact DataTypeVersion semantics, to READY worker-local cache state.
