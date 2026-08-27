# M4 WIP — Object aggregate fingerprint SHA-256 realization

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note freezes the concrete digest realization for the Object aggregate fingerprint used by optimistic preparation and protected commit validation, initially for:

```http
POST /api/v1/core/objects/{object_id}/schema
```

## Semantic source

The fingerprint is derived from the authoritative logical Object aggregate state already frozen for optimistic preparation:

```text
Object intrinsic state
    id
    canonical_name
    template_id
    template_version
    properties

outgoing ownership facts as parent
    child_object_id
    slot_declaring_template_id
    slot_name
```

Derived/enriched read data is excluded.

The logical aggregate is first converted into one deterministic canonical byte representation:

```text
canonical_encode(S) -> bytes
```

Equal logical aggregate state must produce equal bytes and ordering/serialization implementation details must not introduce accidental differences.

## Canonical logical representation reuse

The fingerprint does not invent a second representation for the intrinsic Object state.

For the intrinsic portion, it reuses the same logical/canonical representation already used by the Object GET/public Object representation:

```text
id
canonical_name
object_template
    id
    version
properties
```

Conceptually:

```json
{
  "id": "<object-id>",
  "canonical_name": "server-1",
  "object_template": {
    "id": "<template-id>",
    "version": 4
  },
  "properties": {
    "hostname": "srv01"
  }
}
```

The same canonical Object/property codec must therefore be reused rather than defining an independent fingerprint-only primitive representation.

The fingerprint representation is nevertheless **not identical to the enriched public GET response** because public `components` are a read projection rather than the authoritative ownership facts needed by the concurrency aggregate.

Public Object GET may contain, for example:

```json
"components": {
  "interfaces": [
    {
      "id": "<child-id>",
      "canonical_name": "eth0"
    }
  ],
  "disks": []
}
```

Those values must not be fingerprinted as-is because:

```text
child canonical_name
    -> belongs to the child Object aggregate
    -> child RENAME must not change the parent fingerprint

empty effective slots
    -> come from model-plane effective-schema enrichment
    -> are not current runtime ownership facts

slot_declaring_template_id
    -> is required by runtime ownership semantic identity
    -> is not exposed by the public GET component summary
```

Therefore the canonical fingerprint representation extends the reused intrinsic Object representation with an internal authoritative ownership collection:

```json
{
  "id": "<object-id>",
  "canonical_name": "server-1",
  "object_template": {
    "id": "<template-id>",
    "version": 4
  },
  "properties": {
    "hostname": "srv01"
  },
  "ownership": [
    {
      "child_object_id": "<child-id>",
      "slot_declaring_template_id": "<declaring-template-id>",
      "slot_name": "interfaces"
    }
  ]
}
```

`ownership` is an internal fingerprint/concurrency representation, not a new public API DTO.

The outgoing ownership list is deterministically ordered by:

```text
(slot_declaring_template_id, slot_name, child_object_id)
```

before serialization and hashing.

Frozen representation boundary:

```text
intrinsic Object
    -> reuse Object canonical representation

public GET components
    -> EXCLUDED from fingerprint

internal outgoing ownership facts
    -> INCLUDED using semantic ownership identity
```

## Frozen digest algorithm

The Object aggregate fingerprint is:

```text
ObjectAggregateFingerprint(S)
    = SHA-256(canonical_encode(S))
```

The internal representation is the raw SHA-256 digest:

```text
32 bytes
```

It is not stored or compared as the 64-character hexadecimal representation.

Hexadecimal rendering may be used only for bounded diagnostics/logging and does not participate in equality semantics.

## Why hash instead of carrying the full serialization

The canonical serialized aggregate may grow with Object properties and outgoing ownership edges.

Hashing provides a fixed-size comparison token:

```text
aggregate size      -> variable
canonical bytes     -> variable
SHA-256 fingerprint -> fixed 32 bytes
```

This keeps `PreparedSchemaChange.expected_object_fingerprint` compact and makes protected equality comparison independent of aggregate size once both digests have been computed.

The dominant protected-check cost may still be reading and canonicalizing the aggregate; the design does not claim that the 32-byte comparison itself is the primary performance optimization. The fixed-size digest nevertheless simplifies candidate state, equality comparison, instrumentation and possible future physical optimizations.

## Safety role

SHA-256 is used here as a collision-resistant equality digest, not as an authentication or secrecy primitive.

The concurrency safety condition is:

```text
prepared_fingerprint
    = SHA-256(canonical_encode(S))

protected_current_fingerprint
    = SHA-256(canonical_encode(S'))

protected_current_fingerprint != prepared_fingerprint
    -> stale prepared success
    -> rollback
    -> bounded retry policy

protected_current_fingerprint == prepared_fingerprint
    -> aggregate generations are treated as equivalent for commit admission
```

The protocol therefore relies on both:

```text
1. deterministic canonical encoding
2. SHA-256 collision resistance
```

A non-deterministic serializer would invalidate the protocol even with SHA-256.

## Preparation and protected recheck symmetry

Both sides MUST use the same canonical encoder and digest implementation:

```text
PREPARATION
    coherent aggregate snapshot S
    -> canonical_encode(S)
    -> SHA-256
    -> expected_fingerprint: bytes[32]

PROTECTED Q3
    fresh aggregate snapshot S'
    -> canonical_encode(S')
    -> SHA-256
    -> current_fingerprint: bytes[32]

COMPARE
    current_fingerprint == expected_fingerprint
```

There is no separate DB-side digest definition in M4.

## PostgreSQL boundary

Q3 remains one PostgreSQL statement that reads the authoritative Object intrinsic state plus all outgoing ownership rows needed by the fingerprint.

The digest itself is calculated in the application layer.

M4 does not require:

```text
PostgreSQL digest()/pgcrypto
persisted object fingerprint column
persisted aggregate revision solely for this protocol
trigger-maintained digest
DB-specific binary serialization contract
```

A future benchmark-driven implementation may revisit where hashing occurs, but changing the physical location of the calculation must preserve the exact canonical logical representation and SHA-256 equality semantics frozen here unless architecture is explicitly revised.

## Frozen decision

```text
fingerprint source
    = canonical logical Object aggregate representation

intrinsic Object representation
    = reuse the same Object canonical representation used by GET

public GET components
    = excluded from fingerprint

outgoing ownership representation
    = internal authoritative rows with
      child_object_id + slot_declaring_template_id + slot_name

ownership ordering
    = (slot_declaring_template_id, slot_name, child_object_id)

hash algorithm
    = SHA-256

internal fingerprint size
    = 32 raw bytes

hex form
    = diagnostics only

hash location in M4 TO-BE
    = application layer

comparison
    = exact equality of the two 32-byte digests
```
