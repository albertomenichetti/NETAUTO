# M4 WIP — ObjectTemplate validation-loader architecture handoff

Status: CROSS-DOMAIN ARCHITECTURE HANDOFF / WIP / NON-NORMATIVE GLOBALLY

## Why this note exists

The route-local TO-BE closure for `Object.CREATE` assumes that, after PostgreSQL has resolved one exact ObjectTemplate binding `(template_id, version)`, the worker can bring the stable/immutable semantic knowledge required for direct-creation eligibility and Object property validation into cache through an efficient bounded loader.

This capability was already anticipated by the preliminary M4 Object/ObjectTemplate cache findings, but it is not yet physically or normatively defined.

The assumption must not be lost when the top-down sweep later reaches ObjectTemplate.

## Consumer contract ratified by Object.CREATE

`Object.CREATE` requires the following behavior:

```text
STEP 1
    PostgreSQL resolves exact binding + current PUBLISHED admission

STEP 2
    direct-creation eligibility + property validation consume cache

    required facets READY
        -> check stable abstract semantics
        -> validate immediately

    required facet MISSING or PARTIAL
        -> load/complete immutable/stable semantic knowledge
        -> fill/compile cache
        -> mark required facets READY
        -> validate from cache
```

CREATE must never fall back to recursive ObjectTemplate/DataType persistence traversal or N+1 exact DataType reads in order to validate one Object candidate.

The semantic component facet is not a correctness prerequisite for Object CREATE. However, when the same bounded cold load can obtain the exact effective component semantics without an otherwise unnecessary additional PostgreSQL round trip, CREATE should opportunistically warm that facet too for later consumers of the same exact ObjectTemplateVersion.

Therefore:

```text
CREATE requires
    stable direct-creation eligibility
    validation/property semantics

CREATE cold fill may additionally warm
    exact effective component semantics

component-facet readiness
    != CREATE semantic prerequisite
```

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

Only a complete READY state for the facets required by the consuming operation is consumable by Object runtime validation.

The broader exact ObjectTemplate semantic cache may independently expose a component facet such as:

```text
effective components
    declaring_template_id
    name
    target_template_id
```

That facet may be populated opportunistically during a CREATE-driven cold load when doing so has bounded marginal cost and does not add a PostgreSQL round trip solely for speculative warming.

## Required cold-load properties

The ObjectTemplate phase must decide and norm the physical/materialized read model that makes a cold load efficient.

Target requirements already implied by the Object.CREATE closure:

```text
bounded DB work per exact OTV cold load
no recursive parent-chain reconstruction on the runtime hot/cold path
no per-property / per-DTV N+1 loading
consume M4 effective-schema materialization
bulk-load all semantic knowledge needed for the requested validation/direct-creation facets
opportunistically fill reusable exact DTV cache entries when their payload is already present
opportunistically fill the exact component facet when the same bounded load already carries it or can include it without an extra DB round trip
```

A cache may be facet-partial. For example, the component facet may already be READY while the validation facet is missing, or vice versa.

Required behavior:

```text
required facet missing
    -> complete the required knowledge

unrelated facet missing
    -> do not make it a blocking prerequisite

same bounded load naturally provides another immutable facet
    -> opportunistically publish that facet too

extra PostgreSQL round trip needed only for warming
    -> not required by Object.CREATE
```

This preserves operation-local correctness boundaries while allowing cross-operation cache reuse.

## Authority boundary

This loader/cache is not authority for mutable current lifecycle state.

It must not decide:

```text
current default_version
current ObjectTemplateVersion PUBLISHED/DEPRECATED status
current lineage existence as an admission fact
```

Those remain PostgreSQL current-state responsibilities of the consuming command.

Stable `abstract` semantics are intentionally different: direct-creation eligibility is an Object CREATE predicate, but `abstract` is immutable lineage semantics and may be consumed from the stable/semantic cache without a commit-time lifecycle recheck.

Cached exact semantic knowledge may remain valid after `PUBLISHED -> DEPRECATED` because the exact semantic payload is immutable.

## Architecture-phase deliverables

Before M4 architecture can be considered closed, the ObjectTemplate phase must define and norm:

1. the authoritative relational/materialized source for an exact validation/direct-creation cold load;
2. the minimum query/statement shape and bounded-cost expectation;
3. cache facet structure and READY semantics;
4. interaction with the exact DataTypeVersion cache;
5. fill behavior for missing vs partially populated cache entries;
6. opportunistic cross-facet warming policy, including the no-extra-round-trip rule for CREATE-only warming;
7. concurrency behavior for multiple workers/tasks cold-loading the same exact OTV locally;
8. physical indexes required by the loader, reviewed together with the full ObjectTemplate workload;
9. which model-plane publication/materialization step guarantees that the loader never has to re-certify inheritance/DataType semantics at runtime.

## Dependency classification

This is a cross-domain architecture dependency, not a reason to reopen the ratified `Object.CREATE` caller/semantic contract.

The Object.CREATE direction remains valid under this explicit assumption:

> M4 ObjectTemplate architecture will provide and norm an efficient reusable way to bring the stable direct-creation and validation facets of one exact ObjectTemplateVersion, including required exact DataTypeVersion semantics, to READY worker-local cache state; the same bounded load may opportunistically warm the exact component semantic facet without making that facet a CREATE correctness prerequisite.