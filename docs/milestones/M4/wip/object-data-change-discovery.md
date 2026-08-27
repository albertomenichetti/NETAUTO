# Object.DATA_CHANGE discovery — WIP / NON-NORMATIVE

## Scope

First-phase M4 discovery for factual `Object.DATA_CHANGE`. Lock redesign and concurrency realization remain deferred.

## AS-IS

Current flow after locking the Object:

1. load the current Object;
2. `_validate_persisted_object()` loads the exact ObjectTemplateVersion runtime schema via `_runtime_specs()`;
3. `_runtime_specs()` resolves the exact effective ObjectTemplate schema and exact DataTypeVersion dependencies;
4. current persisted properties are canonicalized again and compared with the stored JSON state;
5. `apply_data_change()` applies SET/REMOVE operations to a complete copy of current properties and canonicalizes the full candidate again;
6. semantic no-op returns without UPDATE/event;
7. a real change updates the complete property map and appends one intrinsic DATA_CHANGE event.

## Finding: pre-recertification is redundant

`apply_data_change()` already canonicalizes the complete resulting candidate under the supplied exact runtime specs. Therefore the separate canonicalization of the already admitted persisted `before.properties` is read-side/mutation-side recertification rather than a requirement for candidate safety.

M4 direction:

> trust the stabilized persisted Object as current source state and validate the complete resulting candidate only.

Representable persisted state remains PostgreSQL current truth. Invariant/audit verification belongs elsewhere, not to every DATA_CHANGE hot path.

## Immutable exact schema loader/cache

DATA_CHANGE is an existing exact binding. It does not require current model admission such as:

- lineage `abstract == false`;
- selected OTV currently PUBLISHED;
- current default selection.

The Object row supplies the exact immutable key:

```text
(template_id, template_version)
```

The same read-through loader established for Object runtime consumers should be used:

```text
load_compiled_object_template(T,V)

cache HIT
    -> return compiled immutable effective schema

cache MISS
    -> one immutable semantic projection
    -> compile runtime structures
    -> populate ObjectTemplate/DataType worker caches
    -> return compiled entry
```

The loader must support immutable PUBLISHED or DEPRECATED exact semantics; lifecycle admission is a caller responsibility and must not be embedded into the semantic loader.

## Candidate hot path

```text
validate operation-set shape
lock Object
load current Object
load_compiled_object_template(template_id, template_version)
apply_data_change(current.properties, operations, compiled runtime specs)

if candidate == current.properties:
    return current
    no UPDATE
    no event

UPDATE complete properties JSONB
INSERT intrinsic DATA_CHANGE event
COMMIT
```

No exact-parent traversal, effective-schema reconstruction, DataType semantic reload, constraint recanonicalization, or persisted-state recertification belongs in the normal DATA_CHANGE path.

## Cache/authority split

```text
PostgreSQL
    current mutable Object state and existence

worker-local immutable caches
    exact effective ObjectTemplate schema
    exact DataType semantic/compiled validators
```

Cache presence never proves current Object existence; PostgreSQL remains authoritative for the factual root.

## Open

- exact interaction with lock-plan redesign;
- exact cache class/eviction/loader implementation;
- whether additional invariant-audit tooling should retain the removed persisted-state recertification outside hot mutation paths.
