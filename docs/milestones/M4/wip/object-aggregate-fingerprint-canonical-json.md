# M4 WIP — Object aggregate fingerprint canonical JSON encoding

Status: FROZEN DISCOVERY INPUT / M4 WIP / NON-NORMATIVE GLOBALLY

This note closes the byte-encoding detail for the Object aggregate fingerprint used by optimistic preparation and protected commit validation.

The owning fingerprint contract remains:

```text
ObjectAggregateFingerprint(S)
    = SHA-256(canonical_encode(S))
```

with a 32-byte raw SHA-256 digest.

## Architectural importance

The exact serializer format is not a separate domain or concurrency concept. Once the logical aggregate representation is frozen, the only correctness requirement on the byte encoding is determinism:

```text
same logical aggregate state
    -> same canonical bytes

different ordering/serializer implementation accidents
    -> must not create different canonical bytes
```

Performance is secondary here. The dominant protected-path cost is expected to be reading and materializing the authoritative Object aggregate; choosing a more exotic binary encoding is not justified without evidence.

## Frozen encoding

M4 uses canonical JSON serialized as UTF-8 bytes:

```text
canonical_encode(S)
    = UTF8(canonical_json(S))
```

The implementation must use one shared canonical serializer for both:

```text
PREPARATION
    S -> canonical JSON UTF-8 -> SHA-256

PROTECTED Q3
    S' -> canonical JSON UTF-8 -> SHA-256
```

No Python object `repr`, dataclass/internal-object serialization, pickle or implementation-specific binary layout participates in the fingerprint contract.

## Logical representation reused

The intrinsic Object portion reuses the same canonical logical representation used by the Object GET representation:

```text
id
canonical_name
object_template
    id
    version
properties
```

The public GET `components` projection is excluded.

Instead the fingerprint adds the authoritative outgoing ownership facts:

```text
ownership[]
    child_object_id
    slot_declaring_template_id
    slot_name
```

ordered deterministically by:

```text
(slot_declaring_template_id, slot_name, child_object_id)
```

## Canonical JSON rules

The canonical serializer must at minimum guarantee:

```text
object/map keys
    -> deterministic ordering

ownership array
    -> already sorted by the frozen ownership ordering

UUID values
    -> canonical textual UUID representation

properties values
    -> reuse the existing canonical Object/property persistence/API codec

whitespace
    -> no semantically irrelevant formatting differences

text encoding
    -> UTF-8
```

The exact library call or JSON implementation is an implementation choice as long as these properties hold identically in preparation and protected Q3.

## Frozen decision

```text
logical aggregate representation
    -> already frozen separately

byte encoding
    -> canonical JSON

text encoding
    -> UTF-8

hash
    -> SHA-256

fingerprint
    -> 32 raw bytes

serializer micro-optimization
    -> implementation detail unless benchmarks show material cost
```

No custom binary fingerprint encoding is introduced in M4 without benchmark evidence that canonical JSON serialization is materially significant.