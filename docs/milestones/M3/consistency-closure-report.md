# M3 — Consistency-closure report

**Status:** CANDIDATE READY FOR REVIEW

This document records the independent post-consolidation consistency audit. It
is evidence, not semantic authority. Reviewer acceptance, consistency-closure
completion, M3 delivery, merge, tag, release, and artifact publication are not
claimed.

## Candidate identity

```text
branch                                  M3
starting reviewer-authorized HEAD       2f091f4ca021153280ed37fad7b4b2cc730195f9
gate specification commit               994414747ef3577e5a6f83bdb62bd2fc9146beff
operational authorization commit        55cccf0a19786a904d4fad48fd614b211ead48af
AUDITED_ASIS_SHA                         2f091f4ca021153280ed37fad7b4b2cc730195f9
owner-correction commits                 none
open consistency findings                0
```

Both named authorization commits are ancestors of the audited SHA. The full
audit and repository gate ran from a clean worktree at exactly
`AUDITED_ASIS_SHA`; no file was edited while that gate ran.

The publication/evidence HEAD is the later documentation-only commit that
contains this report and the candidate-ready status update. Its exact identity
is established after push by equality of local `HEAD`, `origin/M3`, and
`refs/heads/M3` returned by the remote. It is intentionally not embedded here,
which avoids a recursive self-hash. The publication commit changes no current
architecture owner or executable/test semantics.

## Current-owner inventory and hashes

The current architecture corpus contains exactly fifteen files. Each Git blob
below is identical to the corresponding blob in the reviewer-accepted AS-IS
consolidation candidate
`d5b73b892defe554e21dff0c29d1e0e221157d9a`; no owner correction was required.

| Current owner/projection | Bytes | Lines | Git blob | SHA-256 |
|---|---:|---:|---|---|
| `docs/architecture/README.md` | 8,044 | 139 | `9d071e345402420b53cecb61cbddba0d6c5babd8` | `15e399bfbfa5238707c2714febd03f21e9f2c4ea99354eeb75260e55050e9559` |
| `docs/architecture/api.md` | 30,976 | 1,028 | `f11efa6d0b323d3d9f1e8975d22e29b604fa0a13` | `8114ffa244e6b564192fbea4d3e66faf9bc25c3961523ad4d4e7735afd7dabcd` |
| `docs/architecture/cli.md` | 14,387 | 387 | `52cceaebddb9f3648534e7478dca177e128dd343` | `116f88bc10d002119c4787a4e65134effc7af3cca832e002734ee98b0daca2f5` |
| `docs/architecture/concurrency-matrix.md` | 26,475 | 797 | `91baea955eaad8fba76d8821c9f5356d9659acb3` | `ca82af4a11254fedcb6476832b1cfa4d0ea012e3f28cd5ce14e978d7b90ec70c` |
| `docs/architecture/concurrency.md` | 19,882 | 318 | `076e93f490a2f5c514d096daa54c4a361d307b95` | `2f1789c31e8e0fb39765a3bc09c37c68009136812d0a1894a9b05ca518f0497b` |
| `docs/architecture/datatype.md` | 10,416 | 283 | `dc7274f0a78210167fb4aeb43dfdb7b4c942031d` | `20a68522e6d4ccace42f4dedcace251a81a375a1a7bcaea91aeafac75c4286b1` |
| `docs/architecture/health.md` | 5,174 | 140 | `1a1d309ea4e372b0771d7a5cdbd5f73a2d22d323` | `a9a708f271934c71b29bed7c59db9f91b4c267ad1588c056e22f430a08534a5a` |
| `docs/architecture/linux-operating-baseline.md` | 9,925 | 273 | `53527f70d20bda62a32ada3857a6bef11e31703f` | `119c4171005408cbd3cad7c169360e478a368daca18930dea4af8ee3d5a43756` |
| `docs/architecture/object.md` | 15,701 | 389 | `00d9b170552657165ce94ed09463e816338efd35` | `f4cbf03439edd71d89af8c5913b2de9db47a42a061653b4f7b0b66772b84b019` |
| `docs/architecture/objecttemplate.md` | 14,675 | 358 | `7dc98fb9106c56fad96db4bd5bb76804302a1696` | `8d50976eaaf3ca1f97be0f191890d81a5c135926b15ad2746e7f9993c9f703f9` |
| `docs/architecture/persistence.md` | 22,869 | 670 | `b78346468e1164483da6fd93c3b43019889eef89` | `944141355013209bdde8bd96ebed0b045666dd076b489ea28e5f9500fab81947` |
| `docs/architecture/relationship.md` | 22,815 | 644 | `7e709a8063d9f3358e4be8071fef33be90195faa` | `06d1e8075d7b0a637d06e118e8f2a2e7abb8df1a58fcf3b20df2e9455348ed49` |
| `docs/architecture/runtime-deployment.md` | 10,785 | 284 | `35640db026c0fcd1c856cafbe743ca4fa847c87f` | `c36b6928739e34854bc7f72f7a20b56cc8c64fb80e4d81b608522f7241edbc8d` |
| `docs/architecture/verification-concurrency-registry.md` | 23,252 | 413 | `ab2318f7a4fc2d8e4b437fa590a33a157fcc1be7` | `dcdaf535477112bc921cd9c2727f87b58e02aa6d2ea72cef6c34a317d2a581aa` |
| `docs/architecture/verification.md` | 16,654 | 374 | `3945512e45398a6094e33acd4a822fd8d876aa00` | `fdeaf6e4ba0893f66ea4bbbfcc7622c603d3a0eacedbfbd1d8adcc699a8a2394` |

`docs/architecture/README.md` links each of the fourteen owner/projection
documents exactly once in the owner map. The README is the fifteenth control
file.

## Finite consistency matrix

| Key | Required consistency area | Result |
|---|---|---|
| CC-01 | authority topology and owner uniqueness | PASS |
| CC-02 | stable identity, exact versioning, lifecycle and default policy | PASS |
| CC-03 | PrimitiveType, cardinality, canonical value and JSON representation | PASS |
| CC-04 | ObjectTemplate inheritance, declarations, effective schema and trusted reads | PASS |
| CC-05 | Object factual state, ownership, lifecycle and trusted projections | PASS |
| CC-06 | RelationshipDefinition, RDV, factual Relationship and historical decoding | PASS |
| CC-07 | relational schema, codecs, Alembic and public read projection realization | PASS |
| CC-08 | mutation concurrency, lock plans and statement-snapshot boundary | PASS |
| CC-09 | HTTP routes, DTOs, failures, trusted reads, parent filter and cursor protocol | PASS |
| CC-10 | Health semantics, startup compatibility and shared runtime resources | PASS |
| CC-11 | CLI registry, selectors, nullable carriers, Location protocol and process behavior | PASS |
| CC-12 | Settings, distribution, installed migration, trust and Linux operation | PASS |
| CC-13 | verification layers, exact registries, environments and release gates | PASS |
| CC-14 | exclusions, negative surfaces and technology-boundary coherence | PASS |
| CC-15 | documentation hygiene, links, provenance and historical-authority isolation | PASS |

All fifteen cells pass. No result uses `FAIL` or `BLOCKED`.

## Finding registry

```text
findings created   0
open               0
closed             0
blocked            0
owner corrections  0
```

No `M3-CC-Fnn` identifier was created because the audit found no projection
defect, current-owner incompleteness, implementation defect, authority
contradiction, missing decision, or in-scope mismatch.

## Owner and dependency audit

- Authority topology is acyclic and unique. Domain owners define their state
  and invariants; persistence, concurrency, API, CLI, runtime, Linux, and
  verification documents project those decisions without creating a competing
  semantic owner. The Linux document explicitly remains an operator projection
  of the runtime/deployment owner.
- Stable lineage identity, exact version identity, monotonic lifecycle,
  immutable published/deprecated snapshots, nullable same-lineage defaults,
  exact persisted pins, and delete-DRAFT/whole-root distinctions agree across
  domain, persistence, API, and concurrency owners.
- The exact nine-value `PrimitiveType` catalog, scalar/list cardinality,
  canonicalization, optional key absence, JSONB codecs, and historical
  `JsonValue` decoding form one contract. No current owner introduces JSON
  Schema, runtime property EAV, or a second Relationship value codec.
- ObjectTemplate parent pins, declaration identities, effective inheritance,
  migration defaults, clone/revise/publish behavior, dependency admission, and
  trusted aggregate projection agree with persistence and lock-plan ownership.
- Object identity/state, exact template pinning, ownership slot semantics,
  attach/detach behavior, intrinsic and ownership lifecycle events, delete
  blockers, and trusted contextual projections have one meaning. Target
  absence, empty page, and detached null are kept distinct.
- RelationshipDefinition/RDV lifecycle and defaults, stable Resolution
  membership, factual Relationship exact pins, closure, uniqueness, lifecycle,
  delete blockers, trusted reads, and historical decoding agree across their
  owners. No autonomous Resolution/declaration CRUD surface is implied.
- The mutation semantic matrix, PostgreSQL lock-plan realization, and public
  read statement-snapshot boundary retain separate, compatible ownership.
  Public reads do not acquire mutation lock plans for projection coherence.
- Health, startup revision compatibility, runtime resource sharing, Settings,
  distribution, installed migrations, trust boundary, and Linux procedure are
  mutually consistent with the ratified technology baseline.
- Verification retains T0 through T10, real-PostgreSQL material evidence,
  source-isolated installed-wheel T9, exact registries, deterministic
  concurrency recipes, and T10 negative-surface ownership. Skip, xfail, stress,
  sleep, or automatic rerun is not accepted as normative proof.

## Implementation, schema, and finite-registry cross-checks

The current owners were cross-checked against accepted source registries,
OpenAPI, SQLAlchemy metadata, installed Alembic resources, package metadata,
the runtime lock, and permanent verification registries. Exact results were:

| Inventory | Exact result |
|---|---:|
| Current architecture files | 15 |
| Mutation primitives | 41 |
| Semantic family blocks | 15 |
| Unordered concurrency cells | 861 |
| Safety predicates | 21 |
| Canonical concurrency scenarios | 83 |
| Authoritative tables | 15 |
| Business HTTP operations | 63 |
| Health operations | 1 |
| Canonical business GET routes | 22 |
| Cursor-bearing routes | 12 |
| CLI remote operations | 63 |
| CLI 201 + Location operations | 8 |
| CLI local commands | 8 |
| Public error codes | 23 |

The 63 business HTTP operations are exactly 41 mutations plus 22 reads; the
sole Health operation brings the total public OpenAPI census to 64. The CLI
remote-operation set equals the business OpenAPI set exactly.

The installed and declared schema agree on fifteen tables. The only migration
is `0001_m2_kernel`, with `down_revision = None`; base, head, and database
current are all `0001_m2_kernel`. Direct `alembic check` reported no new upgrade
operations, and the schema tests established `compare_metadata == []`. Startup
continues to require exact revision equality and exposes no automatic migrate,
stamp, repair, or alternate compatibility path.

Package version is exactly `0.2.0`. These protected blobs are unchanged:

```text
pyproject.toml  d20bbb94739a74ebfb0bd27291b6e4f130d24c5f
uv.lock         0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23
migration       27fc85e0b4411332fce87c406b6216b35db6eb20
```

## M3-sensitive protocol cross-checks

### Trusted reads and statement snapshots

All 22 canonical public GETs validate request/cursor carriers, classify path
targets, compose persisted facts needed for their projection, and decode
mandatory typed carriers. They do not replay mutation admission or semantic
certification merely to read accepted persisted state. Representable semantic
surprises remain readable; an undecodable mandatory carrier maps to the bounded
public internal-error boundary without repair, invented defaults, or silent
required-member omission.

Each of the 22 routes executes exactly one authoritative business SQL statement
inside an ordinary read Unit of Work. The statement supplies one PostgreSQL
statement snapshot: a writer committed before execution yields the complete
AFTER projection; a writer committing after statement completion and before
application return yields the complete BEFORE projection. The deterministic T3
evidence passed both cuts without a mixed generation. No cross-request
repeatable-membership or public snapshot-token promise is introduced, and
`coherent_read()` remains valid for separately owned uses outside this census.

### Cursor protocol

The API owner, verification owner, cursor registry/codec, implementation, and
tests agree on exactly twelve cursor-bearing routes. Query identity is route
identity plus every membership-affecting path, filter, and presence state;
position is the complete canonical ordering tuple; limit is excluded. In
particular:

```text
object_components     parent_object_id + slot_name / child_object_id
object_relationships  object_id + definition/name / relationship_id + destination_object_id + name
lifecycle              global None vs Object UUID / occurred_at + id DESC
object_templates       parent_template_id + parent_filter_set / namespace + name
```

Cursor codec v1 is unchanged. A changed limit is accepted, while changed
membership identity and malformed keys are rejected.

### ObjectTemplate parent tri-state

HTTP and CLI agree that omission emits no parent predicate/query pair, a UUID
or human selector resolves to the exact stable UUID, and exact lowercase
`null` selects roots. CLI explicit null performs zero selector discovery.
Nullable QUERY `None` serializes to lexical `null` only through nullable
parameter metadata; BODY `None` remains JSON null, PATH `None` is invalid, and
the generic scalar serializer is not broadened.

### CLI Location protocol

Exactly eight create operations own the 201 + Location protocol. The sole
grammar is `{segment(.segment)*}`. Materialization checks exact-key presence in
`request_values` before dotted traversal of response JSON, accepts `str` or
`int` but not `bool`, and performs literal replacement only. Exactly one actual
Location must equal the expected value. Missing, repeated, mismatched, or
unmaterializable values produce `cli_protocol_error`; no hidden post-mutation
GET exists.

## Documentation hygiene and history isolation

Deterministic audits produced:

```text
current owner files                         15 exact
README owner/projection links               14 exact and unique
relative Markdown links checked             36
broken relative links/anchors                0
M3 OUT/AC/VER/CQG/Snn/RF identifiers        0 in current owners
candidate/commit SHA leakage                 0 in current owners
wip semantic-authority references            0 in current owners
unresolved TBD/TODO/FIXME/placeholders       0
stale open/reopen markers                     0
competing owners/dependency cycles            0
conflicting duplicate finite inventories      0
```

Semantic sections are autonomous present-tense current state. Cycle names are
confined to the concise provenance/navigation material in the architecture
README. Historical milestone WIP is not a semantic dependency; retired prompts
and review aids remain historical, while the active closure prompt remains a
non-normative execution aid.

## Environment

```text
kernel       Linux 6.8.0-134-generic x86_64 GNU/Linux
Git          2.43.0
uv           0.12.3
Python       3.14.7
pytest       8.4.2
ruff         0.16.3
pyright      1.1.411
PostgreSQL   16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
FastAPI      0.141.1
SQLAlchemy   2.0.52
Alembic      1.19.1
psycopg      3.3.4
Pydantic     2.13.4
httpx        0.28.1
```

`TEST_DATABASE_URL` was present and used for every material database claim. No
credential or connection string is recorded in this report.

## Build, static, artifact, and test evidence

Every command in this section ran from the clean audited SHA before this report
or status was written.

| Command / gate | Exact result | Wall duration |
|---|---|---:|
| `uv lock --check` | PASS; 46 packages resolved | 0.02 s |
| `uv sync --locked` | PASS; 44 packages checked | 0.03 s |
| `uv build` | PASS; wheel and sdist built | 1.79 s |
| `uv run ruff format --check .` | PASS; 300 files already formatted | 0.07 s |
| `uv run ruff check .` | PASS | 0.06 s |
| `uv run pyright` | PASS; 0 errors, 0 warnings, 0 information | 25.62 s |
| `uv run pytest --collect-only -q` | PASS; 1,010 collected; 1 known warning | 3.56 s wall; 1.84 s pytest |
| Current-AS-IS, documentation-policy, negative-surface, M1/M2/M3 traceability, and M3-S07 lifecycle/evidence selection | PASS; 128 passed | 42.97 s wall; 41.46 s pytest |
| Accepted mapped M3 evidence runner | PASS; 19/19 bundles, 72/72 cases, 45 targets; 0 error/fail/skip/xfail/xpass/rerun/warning | 24.59 s wall; 24.403 s recorded |
| Expanded M3-S00..M3-S07 evidence | PASS; 113 passed | 23.67 s wall; 21.84 s pytest |
| Schema, metadata, migration, and startup-revision tests | PASS; 24 passed; `compare_metadata == []` | 6.54 s wall; 5.05 s pytest |
| Direct Alembic `upgrade head` | PASS | 1.17 s |
| Direct Alembic `current` | PASS; `0001_m2_kernel (head)` | 0.91 s |
| Direct Alembic `check` | PASS; no new upgrade operations | 1.10 s |
| API, DTO, error, OpenAPI, and HTTP composition | PASS; 44 passed | 26.42 s wall; 24.37 s pytest |
| CLI registry, protocol, process, selector, and nullable-carrier tests | PASS; 258 passed | 23.38 s wall; 21.24 s pytest |
| Health, startup, runtime composition, and Settings | PASS; 117 passed; 1 known warning | 11.76 s wall; 9.66 s pytest |
| Installed-wheel/Linux T9 tests | PASS; 20 passed | 53.10 s wall; 51.24 s pytest |
| Real-PostgreSQL material mutation/concurrency suite | PASS; 190 passed | 120.53 s wall; 116.70 s pytest |
| Exact concurrency registry plus one-statement/T3 focused evidence | PASS; 5 passed | 12.56 s wall; 10.51 s pytest |
| `uv run pytest -q -ra -m 'not postgresql'` | PASS; 726 passed, 284 deselected, 1 known warning | 94.86 s wall; 92.92 s pytest |
| `uv run pytest -q -ra` | PASS; 1,010 passed, 1 known warning | 305.04 s wall; 301.53 s pytest |

The full suite's structured concurrency census recorded 314 canonical worker
outcomes, 80 canonical scenario IDs, and 43 focused/ancillary outcomes.
Supported-path `40P01` was zero and unexpected `40001` was zero. The separated
negative control recorded exactly two `40001` outcomes and one `40P01` outcome.
The focused material concurrency suite recorded 312 canonical outcomes across
78 scenario IDs with the same zero forbidden supported-path disposition.

Final normative disposition on the audited SHA:

```text
skip / xfail / rerun                 0 / 0 / 0
supported-path 40P01                 0
unexpected 40001                     0
negative-control 40001 / 40P01       2 / 1
compare_metadata                     []
new unexplained warnings             0
known warnings                       1 Starlette/httpx deprecation
```

### Artifact identities

Artifacts were built for verification only and were not published.

```text
wheel   dist/netauto-0.2.0-py3-none-any.whl
size    170185 bytes
SHA-256 428a2fe05a9905f3794dd15de65667d5506fa5bef2f0568d1ca1dd2b59fb0ba2

sdist   dist/netauto-0.2.0.tar.gz
size    1082771 bytes
SHA-256 f40455396b52c29c3c54c8f6675d3600bb64686771ff51e9b87246766088c6a7
```

The wheel filename, size, and digest equal the required invariant. The sdist is
recorded as the audited-SHA source archive; it is not compared with the earlier
M3-S07 archive because legitimate documentation content affects source-archive
bytes.

## Scope and changed-file inventory

The publication delta is limited to:

```text
docs/milestones/M3/consistency-closure-report.md  created
docs/milestones/M3/status.md                      candidate-state update
```

No `docs/architecture/` owner changed. Production, tests, schema, migration,
dependency, lock, runtime-lock, root README, frozen M3 authority, technology
baseline, and artifact-publication deltas are all zero.

## Reviewer boundary

This is an M3 consistency-closure candidate ready for reviewer inspection. The
reviewer retains ownership of acceptance and the `COMPLETED` state. M3 remains
`NOT DELIVERED`; software implementation, PR creation, merge, tag, release, and
artifact publication remain unauthorized.
