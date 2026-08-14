# M1 — Final Architecture Consistency Review

**Status:** REVIEW COMPLETE — no blocking contradiction identified after final cross-domain/API/persistence/concurrency/test alignment. Global M1 architecture freeze is pending explicit ratification.

## 1. Purpose

This document records the final pre-freeze consistency review of the normative M1 architecture baseline under:

```text
docs/milestones/M1/architecture/
```

The review does not add capability. It verifies that already-ratified semantics and technical contracts agree across domain, persistence, concurrency, PostgreSQL test and public API documents.

Historical `docs.old/` material is explicitly non-normative and was not used to override the M1 baseline.

## 2. Review baseline

The review covered the consolidated M1 chain:

```text
DataType
ObjectTemplate
Object / ownership / lifecycle
Relationship R2

-> persistence PERSIST-01..20
-> concurrency predicates / REALIZE-01..15
-> real PostgreSQL PGTEST-01..04
-> public API API-01..03.11B
```

The review also checked the architecture-index and owner-document status/open-work markers against the current ratified baseline.

## 3. Findings corrected during the review

The following were documentation alignment defects, not new design decisions.

### 3.1 JSON Schema compiler/projection

Final decision:

```text
JSON Schema is not a NETAUTO validation language,
compile target or public schema projection.

No JSON Schema compiler/API/persisted representation is part of M1.
The capability is not retained as an RFE.
```

NETAUTO domain/application validation remains the sole semantic authority.

An internal effective-schema cache or precomputed execution structure may exist only as an implementation/performance optimization if justified by measurements. It is not a JSON Schema capability and not a second validation authority.

Stale or ambiguous compiler markers were removed/clarified in the owning DataType/ObjectTemplate/Object/Relationship/API/index documents.

### 3.2 Object consistency review

The review document still described the real-PostgreSQL test closure only through PGTEST-01..02.

It was aligned to the current closed baseline:

```text
REALIZE-01..15
PGTEST-01..04
API-03.11
```

No Object-specific architecture item remains open.

### 3.3 Relationship consistency review

The review document still listed REST/error work and PGTEST-03 as open.

It was aligned to the current closed baseline:

```text
REALIZE-12..15
PGTEST-01..04
API-03.11
```

No Relationship-specific architecture item remains open.

### 3.4 API companion status

`api-read-contract.md` still described success/failure mapping as the next API point.

It was aligned to API-03.11, which is already ratified and normative in `api-error-contract.md`.

### 3.5 Effective-schema optimization wording

The phrase `compiled representation` was narrowed to:

```text
internal cache or precomputed execution structure
```

and explicitly separated from JSON Schema/public schema language/validation authority.

## 4. Domain consistency outcome

### DataType

Confirmed aligned:

- fixed M1 PrimitiveType catalog;
- exact canonical value semantics;
- exact DTV pinning and lifecycle/default rules;
- strict public primitive lexical forms;
- no JSON Schema validation/compiler dependency.

### ObjectTemplate

Confirmed aligned:

- stable lineage + exact version snapshot model;
- exact parent/DTV pins;
- complete-candidate DRAFT revise semantics;
- derived effective schema as sole model interpretation authority;
- PropertySemanticKey / SlotSemanticKey continuity;
- no authoritative materialized effective schema;
- no JSON Schema compiler/projection.

### Object / ownership / lifecycle

Confirmed aligned:

- stable Object identity/type lineage + exact OTV pin;
- canonical JSONB runtime state;
- operation-specific mutation semantics;
- forward same-lineage SCHEMA_CHANGE with no implicit remediation;
- single-owner acyclic ownership forest;
- exact attach/detach idempotency semantics;
- typed append-only lifecycle semantic-view projection;
- API read/list/error/success semantics match the domain operations.

### Relationship R2

Confirmed aligned:

- Definition/Resolution/factual Relationship/runtime Resolution separation;
- no source/target or forward/reverse semantic authority;
- complete model/runtime resolved closure;
- exact factual-view uniqueness and convergence;
- exact-ID ABA-safe delete;
- semantic-view lifecycle/read projection;
- API command/read/list/error/success contract matches R2 semantics.

## 5. Persistence and concurrency consistency outcome

Confirmed aligned:

```text
13 authoritative PostgreSQL tables
PERSIST-01..20
32 mutation census
19 semantic safety predicates
REALIZE-01..15
READ COMMITTED mutation baseline
owner lock-strength refinement
FK RESTRICT lifetime authority
ownership graph gate
RelationshipDefinition conflict gate
Relationship exact-view arbitration + fresh-UoW convergence
one-statement Relationship lifecycle metadata observation
```

No stale persistence/concurrency design item was identified.

## 6. Real PostgreSQL test consistency outcome

Confirmed aligned:

```text
PGTEST-01 canonical test contract
PGTEST-02 51-scenario census / predicate coverage
PGTEST-03 deterministic real-PG harness contract
PGTEST-04 reusable execution recipes
```

A PGTEST-05 is not planned for fixture/helper/file-layout decomposition. A new PGTEST architecture point is opened only by a genuine architecture-level testing gap.

## 7. Public API consistency outcome

Confirmed aligned:

```text
API-01 application/transport boundary
API-02 canonical 32-mutation route inventory
API-03.1..08 command/wire/primitive contracts
API-03.9 canonical read projections
API-03.10 keyset list/pagination/filter contract
API-03.11 finite failure codes + success HTTP policy
```

No public HTTP/JSON design point remains open.

## 8. Historical baseline separation

`docs.old/` contains historical ADRs and previous architecture/code assumptions, including former JSON Schema/compiler work.

They remain read-only historical material and do not regain authority through implementation convenience or name similarity.

Any implementation conflict is resolved against the normative M1 architecture, not against `docs.old/` or pre-M1 experimental code.

## 9. Review conclusion

No blocking contradiction or unowned M1 architecture decision remains after the corrections above.

The baseline is therefore eligible for the explicit global freeze decision.

This review does **not** itself mark the architecture frozen. Freeze requires a separate ratified decision that changes the baseline state from:

```text
DRAFT / ratified components / review complete
```

to:

```text
M1 ARCHITECTURE FROZEN
```

After freeze, implementation planning may decompose the architecture but may not silently choose different semantics/mechanisms. Any later contradiction or genuine architecture gap requires explicit architecture reopening and documented propagation.
