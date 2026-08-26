# M3 — AS-IS consolidation gate

**Status:** FINAL — reviewer-owned post-acceptance closure specification.

## Purpose and authority boundary

This document owns the **procedure, scope and acceptance conditions** for consolidating the accepted M3 result into the current AS-IS under `docs/architecture/`.

It does not define new product semantics and cannot override:

```text
docs/architecture/
    delivered M2 AS-IS at the start of consolidation

docs/milestones/M3/contract.md
    FINAL / FROZEN M3 contract

docs/milestones/M3/architecture/
    FINAL / FROZEN M3 TO-BE owners

docs/milestones/M3/steps.md
    FINAL / FROZEN implementation decomposition

docs/milestones/M3/acceptance.md
    reviewer-owned accepted final gate

docs/general/technology_baseline.md
    ratified project-wide technology decisions
```

The accepted implementation, public registries, schema, tests and M3-S07 evidence are cross-check evidence. They do not become independent semantic authority.

If the delivered AS-IS, the frozen M3 owners and the accepted result do not resolve to one coherent current-state meaning, the affected consolidation point enters `STOP`. The consolidator must report the contradiction and must not choose the newest document, the current code, a test expectation or the most convenient interpretation.

## Consolidation objective

The output is the autonomous current architecture for the accepted M3 state.

A future milestone or fix must be able to determine, by reading `docs/architecture/` plus the technology baseline:

```text
what the public GET/read responsibility is
how one-request read coherence is realized
which cursor query identities and keysets are current
how historical lifecycle state is decoded
how ObjectTemplate parent filtering behaves in HTTP and CLI
how CLI 201 Location validation works
which previously delivered domain, persistence, concurrency, API, CLI,
runtime and verification guarantees remain unchanged
```

without reconstructing M1, M2 or M3.

The consolidation is **not**:

```text
a changelog
a before/after comparison
a copy of M3 TO-BE documents
a list of implementation commits or slices
a final-acceptance report
a catalogue of M3-VER identifiers, candidate hashes, test counts or durations
a new software or architecture design phase
```

## Non-negotiable current-state rule

Semantic sections use present-tense current-state language.

Invalid style:

```text
M3 changed GETs to ...
Previously reads revalidated ...
The new parent null carrier ...
S04 fixed cursor identity ...
```

Required style:

```text
A public GET validates request/cursor carriers, locates the target, composes persisted facts and decodes mandatory response carriers.
The Object-components cursor identity includes parent_object_id.
parent_template_id=null selects stable root ObjectTemplates.
A registered CLI Location template is materialized by the closed NETAUTO token grammar.
```

Cycle provenance may appear only in the concise provenance section of `docs/architecture/README.md` and in historical links. M3 identifiers do not belong in semantic ownership sections.

## Gate lifecycle

```text
READY
    reviewer has authorized AS-IS consolidation
    docs/architecture remains the delivered pre-M3 AS-IS

IN PROGRESS
    consolidator is deriving and writing the accepted current state

CANDIDATE READY FOR REVIEW
    one complete consolidation candidate is pushed
    preliminary consistency and repository gates are green

REVIEW CHANGES REQUIRED
    reviewer rejected the consolidation candidate
    bounded corrections remain inside this gate

COMPLETED
    reviewer accepted the current AS-IS corpus
    the separate consistency-closure gate may be authorized
```

The coding agent may publish only `CANDIDATE READY FOR REVIEW`. It may not mark this gate `COMPLETED`, may not mark M3 `DELIVERED`, and may not merge, tag, release or publish artifacts.

## Source corpus to read in full

The consolidator must read dependency-first:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

all 15 files under docs/architecture/

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
all normative files under docs/milestones/M3/architecture/
docs/milestones/M3/steps.md
docs/milestones/M3/status.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/evidence/M3-S06-candidate.md
docs/milestones/M3/evidence/M3-S07-candidate.md

accepted public API/OpenAPI and CLI registries
accepted cursor and M3 evidence registries
accepted schema/migration metadata
permanent current verification/concurrency registries
```

Historical M3 `wip/` material is not semantic authority and must not be copied into the current AS-IS. It may be consulted only for provenance/navigation when an owning frozen document explicitly points to it.

## Target corpus and ownership map

The target current architecture corpus remains **exactly 15 files**. M3 adds no new current architecture owner.

| Area | Current owner | Required consolidation action |
|---|---|---|
| Set entry point | `docs/architecture/README.md` | Add concise M3 provenance; replace the old read/corruption principle with the accepted trusted-read/materialization boundary; keep the owner map exact. |
| DataType model | `docs/architecture/datatype.md` | Audit and update read-side responsibility where persisted semantic re-certification is described or implied; mutation semantics remain unchanged. |
| ObjectTemplate model | `docs/architecture/objecttemplate.md` | Audit read/effective-schema/capability current-state wording; preserve exact-version and inheritance semantics; do not duplicate HTTP/CLI carrier rules owned elsewhere. |
| Object model | `docs/architecture/object.md` | Consolidate trusted intrinsic/component/owner/relationship/lifecycle read boundaries, including mandatory contextual materialization and bounded undecodable failures. |
| Relationship model | `docs/architecture/relationship.md` | Consolidate trusted RelationshipDefinition/Relationship factual reads and historical lifecycle decoding while preserving strong mutation semantics. |
| Persistence | `docs/architecture/persistence.md` | Consolidate the one-business-statement canonical GET realization, ordinary read UoW/statement snapshot and representational projection boundary; retain `coherent_read()` only as valid infrastructure outside the canonical public GET census. |
| Semantic concurrency matrix | `docs/architecture/concurrency-matrix.md` | Audit only; M3 does not change the 41-mutation / 861-cell / 21-predicate mutation concurrency contract. |
| PostgreSQL concurrency | `docs/architecture/concurrency.md` | Audit only except cross-references needed to distinguish mutation concurrency from one-statement public read snapshots; no lock-plan redesign. |
| Public HTTP API | `docs/architecture/api.md` | Consolidate the exact 22 GET responsibility, complete 12-route cursor identity/keysets, ObjectTemplate lowercase `null` tri-state, lifecycle scope distinction and preserved strict failures. |
| Core Health | `docs/architecture/health.md` | Audit only; no M3 Health change. |
| Official CLI | `docs/architecture/cli.md` | Consolidate ObjectTemplate explicit-null query semantics and the closed Location materialization/validation grammar for the exact eight 201 operations. |
| Runtime/deployment | `docs/architecture/runtime-deployment.md` | Audit only; no M3 runtime/deployment capability change. |
| Linux operating projection | `docs/architecture/linux-operating-baseline.md` | Audit only; no M3 operating-procedure change. |
| Verification policy | `docs/architecture/verification.md` | Consolidate durable verification obligations for trusted reads, exact 22/12/8 censuses, one-statement snapshots, cursor binding, lifecycle decoding and non-drift without copying M3 evidence bookkeeping. |
| Concurrency verification registry | `docs/architecture/verification-concurrency-registry.md` | Audit only; preserve the exact 83 scenarios / 21 predicates and recipes. |

No additional `docs/architecture/*.md` file may be introduced. A need for a new owner is a reviewer finding/STOP condition, not automatic permission to split ownership.

## Durable identifiers and historical identifiers

The current AS-IS continues to preserve durable identifiers needed by future cycles, including:

```text
canonical mutation names
canonical concurrency scenario IDs
safety-predicate codes
public error codes
route identifiers and route inventories
schema/table/index/constraint identifiers
settings and migration identifiers
cursor route identifiers where they are current protocol evidence
```

The following remain historical M3 record only and must not become current architecture identifiers:

```text
M3-OUT-*
M3-AC-*
M3-VER-*
M3-CQG-*
M3-Snn
S03-RF-* / S07-RF-*
candidate or commit SHA values
exact final-gate pass counts and command durations
```

## Accepted M3 current-state semantics to consolidate

### 1. Public GET/read responsibility

The current public business read surface remains exactly **22 canonical GET/read routes**.

A public read owns:

```text
strict request carrier validation
strict cursor validation
path-target existence classification
lookup/composition of persisted facts required by the public projection
representational decoding required to construct the typed public response
```

A public read does **not** re-certify mutation-owned semantic invariants merely because it is reading persisted state.

Accordingly, current AS-IS must not describe GET as re-running admission/transition/domain validation such as:

```text
default-version publication certification
persisted aggregate mutation-domain validation
inheritance admissibility/cycle/agreement certification
runtime schema/DataType re-resolution solely to prove persisted values again
ownership slot semantic revalidation
Relationship Definition/schema/topology re-certification
historical lifecycle changedness/admissibility/version-increase replay
```

Mutation/write validation remains strong and unchanged in responsibility.

A representable persisted semantic surprise is readable. A mandatory carrier that cannot be materialized into its required public typed form is a bounded internal failure; reads do not repair, invent defaults or silently omit required state.

### 2. One-request committed projection coherence

Each of the 22 canonical public GET/read routes obtains its complete business projection through exactly **one authoritative business SQL statement** in an ordinary read Unit of Work.

The resulting public projection is one PostgreSQL statement snapshot:

```text
writer commits before authoritative statement
    -> complete AFTER projection

writer commits after authoritative statement completes but before application return
    -> complete BEFORE projection
```

A response must not mix incompatible generations of the state projected by that statement.

There is no cross-request repeatable membership guarantee and no public snapshot token. Separate pages/requests may observe different committed memberships.

`coherent_read()` remains valid infrastructure outside the canonical 22 public GET/read census; it is not the dependency of these public GETs and is not globally deprecated.

### 3. Historical lifecycle trusted decoding

Global and Object-scoped lifecycle reads retain their discriminated event DTOs, filters and `(occurred_at, id)` descending ordering.

Historical JSON state is decoded only as required to materialize the public typed event:

```text
required family/discriminant fields
required object/relationship factual fields
UUID/string/integer primitive conversions
recursive JsonValue decoding
```

GET does not replay mutation transition certification such as changedness, semantic admissibility, version increase or agreement with current live state.

Representable historical semantic surprises remain readable. Materially undecodable mandatory historical carriers fail boundedly with the public internal-error boundary.

### 4. Complete cursor identity

The current keyset rule is:

```text
query identity
    = route identity
    + every membership-affecting path target
    + every membership-affecting query filter
    + any semantic presence bit required to distinguish query meaning

position
    = complete canonical ordering tuple

limit
    = excluded from semantic identity
```

The cursor-bearing route census remains exactly 12:

```text
GET /api/v1/core/datatypes
GET /api/v1/core/datatypes/{datatype_id}/versions
GET /api/v1/core/object-templates
GET /api/v1/core/object-templates/{template_id}/versions
GET /api/v1/core/object-templates/{template_id}/relationship-capabilities
GET /api/v1/core/objects
GET /api/v1/core/objects/{parent_object_id}/components
GET /api/v1/core/objects/{object_id}/relationships
GET /api/v1/core/objects/{object_id}/lifecycle-events
GET /api/v1/core/relationship-definitions
GET /api/v1/core/relationship-definitions/{relationship_definition_id}/versions
GET /api/v1/core/lifecycle-events
```

Mandatory current identities include:

```text
object_components
    filters parent_object_id, slot_name
    key child_object_id

object_relationships
    filters object_id, relationship_definition_id, name
    key relationship_id, destination_object_id, name

lifecycle_events
    global involving_object_id=None
    Object-scoped involving_object_id=<path object>
    key occurred_at, id DESC

object_templates
    parent_template_id + parent_filter_set preserve omitted/root/exact-parent distinction
```

Cursor codec v1 remains opaque and unchanged. Incompatible route/filter/path/presence/key carriers return the existing `invalid_cursor` failure. Changing only `limit` remains valid.

### 5. ObjectTemplate parent filter

The one public HTTP filter remains:

```text
parent_template_id omitted
    -> no parent predicate

parent_template_id=<UUID>
    -> direct children of that stable parent

parent_template_id=null
    -> stable root ObjectTemplates only
```

Only exact lowercase lexical `null` is the root sentinel. Empty/malformed/uppercase/special sentinels and repeated values remain invalid requests.

Internal representation is:

```text
omitted   -> parent_template_id=None, parent_filter_set=False
root-only -> parent_template_id=None, parent_filter_set=True
exact     -> parent_template_id=str(UUID), parent_filter_set=True
```

`parent_filter_set` is internal only.

The official CLI exposes the same semantic tri-state:

```text
omitted      -> no query pair and no selector lookup
UUID/human   -> normal bounded ObjectTemplate selector resolution -> UUID query pair
explicit null -> parsed None -> zero selector-discovery GET -> lexical parent_template_id=null
```

Nullable QUERY `None` serializes to lexical `null` only through nullable parameter metadata. Nullable BODY `None` remains JSON null; PATH `None` remains invalid. The generic scalar serializer is not broadened to accept `None` globally.

### 6. Official CLI 201 Location materialization

The exact eight registered `201 Created` operations remain unchanged.

A registered Location template uses the closed NETAUTO grammar:

```text
{segment}
{segment.segment...}
segment = [a-z][a-z0-9_]*
```

Token resolution is:

```text
1. exact request_values key presence wins
2. otherwise traverse the validated response JSON object by dotted path
```

Only `str` and `int` excluding `bool` are materializable token carriers. Replacement is literal; Python `format`/`format_map` semantics are not used.

A successful registered create requires exactly one actual `Location` header equal to the deterministically materialized expected value. Missing/repeated/mismatching/non-materializable Location state is `cli_protocol_error`. Canonical successful responses do not become `cli_internal_error` solely because of local Location processing.

No hidden post-mutation GET is added.

### 7. Preserved non-deltas

The consolidation must preserve current ownership and current-state wording for all unaffected guarantees, including:

```text
63 business HTTP operations + one Health route
41 mutation primitives
15 semantic concurrency family blocks / 861 unordered cells
83 canonical concurrency scenarios / 21 safety predicates
15 PostgreSQL tables and current explicit index/constraint authority
one Alembic root/head/current = 0001_m2_kernel
project version 0.2.0
runtime dependency/uv.lock baseline
mutation locking/retry/atomicity/reference-lifetime guarantees
Health, runtime/deployment and Linux operating boundaries
no native auth/TLS/deployment/backup/observability product capability
```

## Current-state writing rules

Every owner must:

- state present current behavior directly;
- preserve one clear semantic owner per decision;
- distinguish semantic state from persistence and wire representation;
- contain exact finite inventories where the surface is closed;
- link to another current owner rather than duplicate its rules;
- contain no unresolved `TODO`, `TBD`, `FIXME`, candidate or open semantic point;
- require no M1/M2/M3 reconstruction to understand current behavior;
- avoid candidate hashes, review findings, M3 evidence IDs and execution counts;
- avoid module-by-module implementation tours unless an entrypoint/package boundary is architectural.

Words such as `M3`, `new`, `changed`, `introduced`, `previously`, `before M3`, `after M3`, `M3 delta`, `candidate`, `to be implemented` are invalid in semantic sections except in the concise README provenance/update-discipline context.

Blind global replacement is forbidden. Rewrite the meaning as current state.

## Cross-document consistency rules

At minimum verify:

```text
README owner map == exact 15-file AS-IS corpus
README provenance includes M1 / M2 / M3 without semantic duplication
GET route inventory == current business registry/OpenAPI evidence == 22
business HTTP inventory remains 63 and Health remains exactly one separate route
CLI remote inventory remains equal to business API inventory
cursor route matrix == exact 12 current identities/keysets
ObjectTemplate HTTP and CLI tri-state semantics agree
CLI 201 Location matrix == exact eight registered creates
public read responsibility agrees across model/API/persistence/verification owners
one-statement/snapshot wording agrees across persistence/API/verification
lifecycle decoder boundary agrees across Object/Relationship/API/persistence/verification
schema/table/index/migration inventory remains delivered 15-table / one-head state
mutation concurrency matrix/lock-plan/scenario/predicate owners remain unchanged and mutually exact
settings/runtime/operator-guide ownership remains unchanged
all internal links resolve inside current AS-IS or technology baseline
```

Cross-cutting consequences may be repeated only as references or concise constraints. Repetition must not create a second competing normative definition.

## Allowed repository delta

The consolidation candidate may modify only:

```text
docs/architecture/*.md
docs/milestones/M3/status.md
```

The exact target architecture inventory remains the existing 15 files; no new architecture file is authorized.

Do not modify:

```text
src/netauto/
tests/
pyproject.toml
uv.lock
schema or migrations
README.md root
AGENTS.md
docs/general/
docs/milestones/M3/contract.md
docs/milestones/M3/architecture/
docs/milestones/M3/steps.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/evidence/
docs/milestones/M3/as-is-consolidation.md
```

A need to modify code, tests, schema, frozen M3 authority, accepted evidence or project-wide technology is `STOP`, not consolidation scope.

## Preliminary consistency and verification gate

Before publishing a candidate, execute at least:

```text
exact 15-file architecture inventory audit
internal Markdown link/reference audit
present-tense / temporal-delta wording audit with README provenance allowlist
milestone-ID leakage audit
normative placeholder/open-owner audit
owner duplication/conflict audit
API GET/business/Health inventory cross-check
12-route cursor matrix cross-check
HTTP/CLI ObjectTemplate tri-state cross-check
8-operation CLI Location cross-check
read responsibility / persistence / lifecycle boundary cross-check
schema / migration / metadata non-drift cross-check
concurrency matrix / lock plan / scenario / predicate non-drift cross-check
settings / runtime / operator-guide non-drift cross-check
```

Then execute repository verification sufficient to prove documentation changes did not create drift, including at minimum:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q

M3 traceability/final-acceptance lifecycle tests
architecture/documentation policy and current-AS-IS traceability tests
accepted M3 evidence modules where documentation ownership is referenced
schema/migration/API/CLI focused regressions
non-PostgreSQL suite
full repository suite with TEST_DATABASE_URL available
```

Required candidate disposition:

```text
normative skip / xfail / rerun   0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
schema compare_metadata          []
new unexplained warning          0
broken internal links            0
unresolved normative placeholder 0
open consolidation finding       0
production/schema/dependency delta 0
```

The exact commands, counts, environment and durations are candidate evidence, not current architecture semantics.

## Candidate publication and reviewer handoff

The consolidator must produce one commit that contains the complete `docs/architecture/` candidate plus the operational `status.md` transition to `CANDIDATE READY FOR REVIEW`.

The handoff must report at minimum:

```text
candidate SHA
changed architecture files / unchanged audited files
exact 15-file inventory
link audit result
milestone/temporal wording audit result
owner/conflict audit result
22 GET / 12 cursor / 8 CLI Location cross-check result
15-table / Alembic non-drift result
83 scenario / 21 predicate non-drift result
build/static/test gate result
skip/xfail/rerun/warning census
production/schema/dependency changes = none
working tree / origin synchronization
PR state
```

The implementer may mark only:

```text
AS-IS consolidation = CANDIDATE READY FOR REVIEW
M3 = NOT DELIVERED
```

Reviewer alone may mark consolidation `COMPLETED` and authorize consistency closure.

## Completion condition

The reviewer may accept the consolidation only when:

```text
all 15 current architecture files form one autonomous current-state corpus
M3 accepted semantics are fully represented without temporal narration
all unaffected delivered guarantees remain exact
one semantic owner exists for each decision
GET/read, cursor, lifecycle, parent-filter and CLI Location boundaries are coherent across owners
no M3 outcome/AC/VER/slice/finding/candidate identifier leaks into semantic ownership
no current behavior requires consulting milestone documents
internal links and inventories are exact
repository verification remains green
no code/test/schema/dependency/frozen-authority modification was required
blocking consolidation findings = 0
```

On reviewer acceptance:

```text
AS-IS consolidation -> COMPLETED
consistency closure  -> may become the next separately authorized gate
M3                   -> remains NOT DELIVERED
software implementation -> remains NOT AUTHORIZED
```

Delivery, merge, tag, release and artifact publication remain separate governance actions.