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

The exact canonical encoding rules are a separate follow-up freeze. They must guarantee that equal logical aggregate state produces equal bytes and that ordering/serialization implementation details do not introduce accidental differences.

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

canonical representation
    = deterministic byte sequence; exact encoding rules follow separately

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
