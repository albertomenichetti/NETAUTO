# Object — Current AS-IS

## Responsibility

An `Object` is a runtime entity with stable identity, stable ObjectTemplate lineage assignment, an exact current ObjectTemplateVersion pin and canonical mutable property state.

Current intrinsic state:

```text
id
canonical_name
template_id
template_version
properties
```

Ownership/component state and Relationship state are separate relational domains and are not embedded in the intrinsic Object snapshot.

## Identity and type assignment

`Object.id` is the authoritative immutable entity identity.

Current generation contract:

- kernel/application generated UUIDv4;
- never caller-supplied;
- opaque and non-semantic;
- no separate historical non-reuse infrastructure beyond UUID generation and current PK authority.

External cloud/resource/serial/legacy identifiers are distinct domain data and are never aliases for `Object.id`.

`template_id` is the stable runtime type assignment. Normal current operations do not reclassify an Object to another ObjectTemplate lineage.

`template_version` is the exact schema snapshot currently governing the Object.

No floating default/latest selector is persisted. Any implicit version selection is resolved at admission time and materialized as an exact `(template_id, template_version)` pin.

`canonical_name` is mutable human/search metadata:

- required current state;
- semantic length `1..255`;
- not unique;
- not an alternative Object identity;
- no automatic normalization.

When CREATE omits `canonical_name`, the command uses the Object UUID string as fallback. Explicit null, empty or invalid input is not omission and fails.

## CREATE admission and definitive closure

CREATE supports explicit and implicit exact version selection.

```text
explicit
    template_id = T
    template_version = V

implicit
    template_id = T
    template_version omitted
    -> T.default_version
```

The selected exact ObjectTemplateVersion must:

- exist in the selected lineage;
- belong to a lineage with `abstract=false`;
- remain `PUBLISHED` through commit.

If implicit resolution finds `default_version = NULL`, CREATE fails even when other PUBLISHED versions exist. There is no highest/latest fallback.

The persisted Object always materializes the selected exact version.

Object validation uses a **definitive exact closure** derived exclusively from:

```text
selected exact ObjectTemplateVersion
-> exact parent ObjectTemplateVersion pins
-> effective property declarations
-> exact DataTypeVersion pins
```

It never consults ObjectTemplate/DataType current defaults, latest or highest versions while resolving the closure.

The selected PUBLISHED ObjectTemplateVersion is the model-plane consistency anchor. CREATE verifies integrity and current Object data validity, but does not recursively re-certify or lifecycle-lock every already-certified ancestor/DataType dependency.

Missing exact dependencies, inheritance corruption or malformed effective schema are internal invariant failures, not caller-selectable fallback conditions.

## Canonical runtime properties

`properties` is the complete current intrinsic value state expressed with canonical primitive representations.

Rules:

- only properties in the current exact effective schema may be present;
- required properties must satisfy presence/cardinality requirements;
- values must satisfy the exact DataTypeVersion contract pinned by the schema;
- JSON `null` is not a runtime property value;
- optional zero-cardinality LIST state canonicalizes to property absence;
- LIST ordering is semantic; JSON object key ordering is not;
- unknown properties are invalid.

CREATE validates caller-supplied state against the selected exact schema. ObjectTemplate `migration_default` is **not** an Object CREATE default mechanism: every required CREATE value must be supplied by the caller unless another command-specific rule explicitly provides it.

## Semantic mutation surface

```text
CREATE
RENAME
DATA_CHANGE
SCHEMA_CHANGE
ATTACH
DETACH
DELETE
```

There is no generic Object PATCH/update operation and no generic Object `state_revision`.

Each mutation owns one semantic Unit of Work and one concurrency contract.

### RENAME

Changes only `canonical_name` and preserves Object identity, exact schema pin, properties, ownership and Relationships.

### DATA_CHANGE

Applies a non-empty semantic operation set over current properties.

Public operations are per-property `SET` or `REMOVE`; at most one operation for the same property may appear in a command. Array order does not define mutation order.

The candidate is derived from the complete current Object state after stabilization and must produce a complete valid state under the same exact schema.

A semantic no-op is successful but emits no fake lifecycle transition.

## Schema change

`SCHEMA_CHANGE` is an explicit forward migration within the same stable ObjectTemplate lineage.

```text
source = current exact OTV
target = exact same-lineage OTV
target_version > source_version
```

The target need not be the immediately following version. Intermediate versions are not traversed as an artificial migration chain.

The target exact version must remain PUBLISHED through commit. The source may be PUBLISHED or DEPRECATED because it is an existing exact binding, not a new admission.

Source and target closures are definitive exact closures. They traverse exact parent and DataTypeVersion pins only; current defaults/latest/highest are never consulted.

The migration derives the target state from the complete current committed Object after locking/stabilization. There is no arbitrary remediation payload.

### Property continuity

Property continuity uses:

```text
PropertySemanticKey = (declaring_template_id, name)
```

not merely the effective name.

For a target property:

- matching semantic source value present: preserve the value or apply only the allowed `SCALAR -> LIST` shape widening, then validate/canonicalize against the target exact DataTypeVersion;
- matching semantic source value absent: optional remains absent; required uses the target `migration_default`;
- semantically new target property: optional absent; required uses target `migration_default`.

A source value that exists but is incompatible with the target contract causes schema-change failure. `migration_default` fills absence only and never overwrites existing incompatible information.

A source-only semantic property is removed from the resulting runtime state. There is no extras/archive/preservation bucket.

The same effective name with a different declaring lineage is a different semantic property. The source value is treated as removed and the target property as new; name coincidence does not create carry-forward.

No implicit value transformation, type coercion, caller-provided target override or preservation side channel occurs.

### Ownership continuity

Outgoing ownership edges must remain valid against the target effective schema.

```text
SlotSemanticKey = (declaring_template_id, slot_name)
```

A schema change cannot commit if an outgoing edge would lose the same current semantic slot or its child would become incompatible.

Schema change never implicitly detaches children. A persisted edge that cannot be resolved against the Object's current exact schema is invariant corruption, not supported legacy state.

Incoming ownership does not require revalidation merely because the child changes exact schema: stable `template_id` remains unchanged.

## Ownership

Ownership is modeled by runtime edges from parent Object to child Object through a current effective component slot.

Current guarantees:

```text
child has at most one owner
ownership graph is acyclic
parent != child
edge resolves to exactly one current effective slot
child lineage is compatible with slot target lineage
```

The child remains a first-class Object with its own identity and exact schema pin.

### ATTACH

ATTACH identifies:

```text
parent object
slot_name
child_object_id
```

It validates the parent's current exact effective schema and child stable-lineage compatibility.

If the exact same edge is already current, ATTACH converges successfully without duplicate state or lifecycle events.

If the child is owned elsewhere, ATTACH fails and does not perform an implicit move.

Concurrent different-owner ATTACH attempts are resolved by the single-owner persistence authority and fresh semantic re-evaluation.

A graph-wide ownership edge-add gate protects acyclicity against races where individually valid candidate edges could jointly create a cycle.

### DETACH

DETACH removes only the requested exact current edge.

An already-detached exact request is an idempotent success.

DETACH does not repeat ATTACH-style compatibility admission. When a real current edge exists, it resolves the current slot semantic key from the stabilized parent schema for projection/lifecycle semantics.

A current edge that does not resolve against the current parent schema is internal invariant corruption; DETACH does not perform historical slot lookup.

Edge removal cannot introduce a cycle and therefore does not use the ownership cycle-add gate.

## Delete semantics

Object DELETE removes only the requested Object; there is no subtree delete or cascade/force public option.

Delete is admissible only when the Object has no current reference requiring its lifetime, including:

- incoming ownership edge;
- outgoing ownership edge;
- current factual Relationship association;
- other current cross-aggregate references protected by persistence.

A delete does not implicitly detach ownership or delete Relationships to become admissible.

## Lifecycle changelog

Intrinsic and structural Object-related transitions produce one unified append-only lifecycle stream.

A real semantic mutation and its complete required lifecycle event set are atomic:

```text
current-state transition
+
all required lifecycle event rows
-> commit together
or
-> rollback together
```

Historical event identifiers and names are historical data rather than live current-domain references.

Intrinsic events carry canonical before/after Object snapshots. Structural ownership/Relationship events use typed semantic metadata.

Event ordering is deterministic by `(occurred_at, id)`, while `occurred_at` is a transaction timestamp and not a global commit sequence.

The lifecycle public surface is read-only.

## Relationship interaction

Relationship validity depends on the Object's stable `template_id` lineage, not its current exact version, property state or ownership state.

Object schema change therefore does not invalidate a Relationship when stable lineage assignment remains unchanged.

Object DELETE cannot commit while a current factual Relationship references the Object.

## Read projections

```text
Object GET
    -> intrinsic current state only

components
    -> outgoing ownership semantic projections

owner
    -> zero-or-one incoming ownership projection
    -> existing detached Object returns null

relationships
    -> deduplicated semantic ObjectRelationshipView projections

lifecycle-events
    -> historical discriminated event-family projections
```

Raw ownership rows and raw runtime Relationship-resolution rows are not public representations.

## Concurrency ownership

The Object row is the concurrency owner of complete intrinsic Object state.

```text
RENAME / DATA_CHANGE / SCHEMA_CHANGE
    -> Object row FOR NO KEY UPDATE

DELETE
    -> Object row FOR UPDATE

ATTACH / DETACH / parent SCHEMA_CHANGE
    -> parent Object row FOR NO KEY UPDATE
```

After lock acquisition, current state is reloaded and the candidate is rederived/revalidated. SCHEMA_CHANGE additionally admits the exact target PUBLISHED ObjectTemplateVersion through lifecycle-sensitive dependency admission.

Details and cross-operation predicates are owned by `concurrency.md` and `concurrency-matrix.md`.

## Key invariants

- Object identity is kernel-generated UUIDv4 and immutable;
- stable type lineage does not change through normal operations;
- direct creation targets a non-abstract lineage and an exact PUBLISHED version through commit;
- every Object persists an exact current ObjectTemplateVersion pin;
- definitive schema closure uses exact persisted pins only;
- current properties are canonical and completely valid under that exact schema;
- no unknown properties or JSON null runtime values are persisted;
- schema change is forward, same-lineage and explicit;
- existing source information is preserved or migration fails;
- migration defaults fill absence only;
- source-only properties are removed; no implicit preservation bucket exists;
- schema change never performs implicit detach/remediation;
- every current ownership edge is valid against the parent's current exact effective schema;
- each child has at most one owner and the committed ownership graph is acyclic;
- Object DELETE requires current structural/reference isolation and never performs subtree deletion;
- lifecycle event sets are append-only and atomic with their owning real mutation;
- supported concurrent interleavings preserve all invariants above.