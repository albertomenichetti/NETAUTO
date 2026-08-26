# Codex prompt — M3 consistency closure

**Status:** NON-NORMATIVE POST-CONSOLIDATION EXECUTION AID.

This execution aid is subordinate to `AGENTS.md`, `docs/general/linee_guida_progetto.md`, the accepted current AS-IS under `docs/architecture/`, the FINAL/FROZEN M3 historical authorities, the reviewer-owned final acceptance, the accepted AS-IS consolidation, and the consistency-closure specification in `docs/milestones/M3/consistency-closure.md`.

If this prompt conflicts with an owning authority, stop the affected path and report the conflict. Do not reinterpret current semantics to make the audit pass.

---

# Assignment

Execute exactly:

```text
M3 post-consolidation consistency closure
```

Work directly on branch:

```text
M3
```

The reviewer-owned gate specification is:

```text
994414747ef3577e5a6f83bdb62bd2fc9146beff
docs(m3): define consistency-closure gate
```

Operational authorization is:

```text
55cccf0a19786a904d4fad48fd614b211ead48af
Authorize M3 consistency closure
```

Work from current `origin/M3`; do not reset to either baseline. Confirm both commits remain in ancestry.

Current governance is exactly:

```text
M3-S00 .. M3-S07    reviewer-owned COMPLETED
final acceptance     ACCEPTED
AS-IS consolidation  COMPLETED
consistency closure  READY / AUTHORIZED
software implementation NOT AUTHORIZED
M3                   NOT DELIVERED
```

Do not create a PR. Do not merge, rebase, force-push, tag, release or publish artifacts.

Do not mark consistency closure `COMPLETED`. Do not mark M3 `DELIVERED`.

---

# 1. Mandatory pre-flight

Before changing any file, read in full and obey:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
all fourteen files linked by its owner map

docs/milestones/M3/contract.md
docs/milestones/M3/architecture/README.md
all normative files under docs/milestones/M3/architecture/
docs/milestones/M3/steps.md
docs/milestones/M3/status.md
docs/milestones/M3/acceptance.md
docs/milestones/M3/as-is-consolidation.md
docs/milestones/M3/consistency-closure.md
docs/milestones/M3/evidence/M3-S06-candidate.md
docs/milestones/M3/evidence/M3-S07-candidate.md

accepted API/OpenAPI/CLI/cursor registries
SQLAlchemy metadata and installed Alembic graph
Settings/package metadata/runtime lock
permanent current verification/concurrency registries
```

Historical M3 WIP is non-authoritative. Read it only if needed to prove retirement or trace provenance from a normative owner; never copy semantics from it into current AS-IS.

Pre-flight must confirm:

```text
branch                         M3
origin ancestry                includes authorization
contract                       FINAL / FROZEN
architecture set               FINAL / FROZEN
steps                          FINAL / FROZEN
M3-S00..S07                    COMPLETED
final acceptance               ACCEPTED
AS-IS consolidation            COMPLETED
consistency closure            READY or IN PROGRESS
software implementation        NOT AUTHORIZED
M3                             NOT DELIVERED
current AS-IS files            exactly 15
open incompatible reopen       none
TEST_DATABASE_URL              available
```

When actual audit work starts, `status.md` may move consistency closure from `READY` to `IN PROGRESS`. Keep `M3-S07 COMPLETED`, software `NOT AUTHORIZED`, and M3 `NOT DELIVERED`.

---

# 2. Authority and mismatch discipline

For every claim:

```text
current owner
    -> dependent current owners
    -> technology baseline where applicable
    -> frozen M3 / accepted implementation only as cross-check evidence
```

Classify every mismatch before editing:

```text
projection defect
current-owner incompleteness
implementation defect
architecture contradiction/missing decision
new improvement opportunity
```

Only the first two classes may permit a bounded current-document correction, and only when one unambiguous accepted meaning exists.

Implementation defect, authority contradiction, new semantic owner, product/schema/dependency change, test redefinition or technology change is STOP. Report the issue; do not patch around it.

---

# 3. Hard write scope

## Default

If no consistency finding requires correction, modify only:

```text
docs/milestones/M3/consistency-closure-report.md
docs/milestones/M3/status.md
```

## Conditional current-owner correction

A `docs/architecture/*.md` file may change only after creating a concrete `M3-CC-Fnn` finding and proving:

```text
one current owner is unambiguous
accepted/frozen evidence confirms the same meaning
correction is lossless propagation/clarification
all dependent owners were re-read
report records the finding and exact correction
```

Do not touch unrelated current owners.

## Forbidden

Do not modify:

```text
src/
tests/
pyproject.toml
uv.lock
runtime lock
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
docs/milestones/M3/consistency-closure.md
```

If a test change appears necessary, STOP and report the verification gap; this gate does not authorize test changes.

---

# 4. Exact fifteen-cell consistency matrix

Audit and report every exact key:

```text
CC-01  authority topology and owner uniqueness
CC-02  stable identity, exact versioning, lifecycle and default policy
CC-03  PrimitiveType, cardinality, canonical value and JSON representation
CC-04  ObjectTemplate inheritance, declarations, effective schema and trusted reads
CC-05  Object factual state, ownership, lifecycle and trusted projections
CC-06  RelationshipDefinition, RDV, factual Relationship and historical decoding
CC-07  relational schema, codecs, Alembic and public read projection realization
CC-08  mutation concurrency, lock plans and statement-snapshot boundary
CC-09  HTTP routes, DTOs, failures, trusted reads, parent filter and cursor protocol
CC-10  Health semantics, startup compatibility and shared runtime resources
CC-11  CLI registry, selectors, nullable carriers, Location protocol and process behavior
CC-12  Settings, distribution, installed migration, trust and Linux operation
CC-13  verification layers, exact registries, environments and release gates
CC-14  exclusions, negative surfaces and technology-boundary coherence
CC-15  documentation hygiene, links, provenance and historical-authority isolation
```

Result vocabulary is exactly:

```text
PASS
FAIL:<M3-CC-Fnn>
BLOCKED:<M3-CC-Fnn>
```

A candidate-ready handoff requires all 15 `PASS` and zero open findings.

The gate specification contains the mandatory checks for each cell. Do not reduce them to counts only; inspect semantic agreement.

---

# 5. M3-sensitive consistency checks

The following are high-risk and must be checked explicitly across all relevant current owners.

## Trusted reads

One current meaning must hold:

```text
public GET validates request/cursor carriers
classifies path targets
composes persisted facts needed by the projection
decodes mandatory typed carriers

public GET does not replay mutation semantic admission/certification merely to read state
representable persisted semantic surprise remains readable
materially undecodable mandatory carrier fails boundedly
no repair/default invention/silent required-member omission
```

Mutation invariants remain strong and unchanged.

## One-statement coherence

Verify:

```text
22 / 22 canonical business GETs
ordinary read UoW
exactly one authoritative business SQL statement each
one PostgreSQL statement snapshot
writer before execute -> complete AFTER
writer after statement before return -> complete BEFORE
no mixed generation
no cross-request repeatability/snapshot token
coherent_read() remains valid outside the canonical census where explicitly owned
```

## Cursor protocol

Verify exact 12-route set and identity/keyset agreement across API/current verification/cursor registries/code:

```text
identity = route + membership-affecting path + filter + presence state
position = complete canonical ordering tuple
limit excluded

object_components      parent_object_id + slot_name / child_object_id
object_relationships   object_id + definition/name / relationship_id + destination_object_id + name
lifecycle              global None vs Object UUID / occurred_at + id DESC
object_templates       parent_template_id + parent_filter_set / namespace + name
```

Cursor codec v1 remains unchanged.

## ObjectTemplate parent tri-state

HTTP and CLI must agree:

```text
omitted -> no parent predicate/query pair
UUID/human selector -> exact stable UUID
exact lowercase null -> roots only
```

CLI explicit null performs zero selector discovery. Nullable QUERY None is lexical `null` only through nullable parameter metadata. Nullable BODY None remains JSON null; PATH None invalid; generic scalar serializer not broadened.

## CLI Location protocol

Verify exact eight create operations and one current grammar:

```text
{segment(.segment)*}
request_values exact-key presence first
otherwise response JSON dotted traversal
str/int excluding bool only
literal replacement
exactly one actual Location equal expected
missing/repeated/mismatch/unmaterializable -> cli_protocol_error
no hidden post-mutation GET
```

---

# 6. Exact current finite inventories

Require exact equality, not minimum counts:

```text
current architecture files       15
mutation primitives              41
semantic family blocks           15
unordered concurrency cells     861
safety predicates                21
canonical concurrency scenarios  83
authoritative tables             15
business HTTP operations         63
Health operations                 1
canonical business GET routes    22
cursor-bearing routes            12
CLI remote operations            63
CLI 201 + Location operations     8
CLI local commands                8
public error codes               23
Alembic base/head/current         0001_m2_kernel
project version                   0.2.0
```

Check actual current registries/metadata, not documentation counts alone.

---

# 7. Finding registry

Use IDs:

```text
M3-CC-F01
M3-CC-F02
...
```

Every finding must record:

```text
ID
matrix cell
classification
owners involved
exact contradictory/missing statements
cross-check evidence
resolution or STOP reason
files changed, if any
status OPEN / CLOSED / BLOCKED
```

Findings are historical closure evidence and must never leak into `docs/architecture/`.

If a finding requires a current-owner correction, make that correction in a dedicated commit before selecting the audited SHA. Rerun the entire closure gate after the correction.

---

# 8. Immutable AUDITED_ASIS_SHA

Define one exact audit candidate:

```text
AUDITED_ASIS_SHA
```

If there are no owner corrections, it is the clean current closure work HEAD before report/status publication.

If there are owner corrections:

```text
classify finding
apply bounded correction
commit correction
freeze resulting SHA as AUDITED_ASIS_SHA
```

Then run the complete gate from a clean worktree at exactly that SHA.

Before the gate:

```text
git status --short -> empty
HEAD -> AUDITED_ASIS_SHA
```

During the gate, do not edit files. Any needed edit abandons that audited SHA; commit a replacement and restart the full gate.

---

# 9. Required closure report

Create after the complete gate passes:

```text
docs/milestones/M3/consistency-closure-report.md
```

It must contain at minimum:

```text
Status: CANDIDATE READY FOR REVIEW
branch
starting authorization HEAD
AUDITED_ASIS_SHA
publication/evidence HEAD model
exact fifteen-file owner inventory + Git blob/content hashes
CC-01..CC-15 table
finding registry; open findings = 0
owner/dependency audit summary
implementation/schema/public-registry cross-check summary
trusted-read/statement/cursor/parent-null/Location cross-check summary
document hygiene/link/WIP-isolation audit
runtime/toolchain versions
exact commands, counts, durations and results
wheel filename/size/SHA-256
sdist filename/size/SHA-256
scope/changed-file inventory
reviewer boundary
```

Do not claim reviewer acceptance, `COMPLETED`, M3 delivery or merge.

---

# 10. Static documentation audits

Execute deterministic bounded audits for:

```text
15-file corpus exactness
README owner map exactness and uniqueness
Markdown relative-link/anchor validity
owner dependency cycles/competing ownership
temporal/change-log wording
M1/M2/M3 leakage outside concise provenance/history links
M3-OUT/AC/VER/CQG/Snn/RF/candidate/commit leakage into semantic owners
TBD/TODO/FIXME/open/placeholder wording
duplicate finite inventories with conflicting values
current owner references to wip as authority
```

Temporary scripts are allowed but must not be committed.

---

# 11. Required build/static and artifact gate

From clean `AUDITED_ASIS_SHA` run at minimum:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Record exact output/census/duration.

Wheel identity must remain exactly:

```text
netauto-0.2.0-py3-none-any.whl
170185 bytes
SHA-256 428a2fe05a9905f3794dd15de65667d5506fa5bef2f0568d1ca1dd2b59fb0ba2
```

Also verify unchanged:

```text
project version 0.2.0
pyproject.toml blob d20bbb94739a74ebfb0bd27291b6e4f130d24c5f
uv.lock blob        0aa980926fda5f42ee3a7d3cedc64f9fcf8c2d23
migration blob      27fc85e0b4411332fce87c406b6216b35db6eb20
```

Record the current sdist identity, but do **not** require equality with the S07 sdist because documentation/report content legitimately changes source-archive bytes.

Do not publish artifacts.

---

# 12. Required repository verification

`TEST_DATABASE_URL` is mandatory for the final closure candidate.

Execute at minimum:

```text
current-AS-IS/documentation-policy and negative-surface tests
M1/M2/M3 traceability tests
M3-S07 final-acceptance lifecycle/evidence tests
accepted M3 evidence selection
schema/metadata/migration/startup-revision tests
API/DTO/error/OpenAPI tests
CLI registry/protocol/process tests
Health/runtime composition tests
installed-wheel/Linux T9 tests
real-PostgreSQL material mutation/concurrency tests
22-route statement census + deterministic T3 BEFORE/AFTER evidence
non-PostgreSQL suite
full repository suite
```

Use exact current targets discovered from permanent registries and existing project tests rather than inventing duplicate semantic test maps.

Required final disposition:

```text
skip / xfail / rerun = 0 / 0 / 0
supported-path 40P01 = 0
unexpected 40001 = 0
negative-control SQLSTATE exact expected census
compare_metadata == []
new unexplained warning = 0
```

The previously reviewed Starlette deprecation may remain the sole known warning.

Do not claim PASS for an unexecuted or PostgreSQL-blocked requirement.

---

# 13. Candidate publication discipline

Once all fifteen cells and repository gates pass on `AUDITED_ASIS_SHA`:

1. create/update `docs/milestones/M3/consistency-closure-report.md`;
2. update `docs/milestones/M3/status.md` to:

```text
AS-IS consolidation   COMPLETED
consistency closure   CANDIDATE READY FOR REVIEW
M3                    NOT DELIVERED
software implementation NOT AUTHORIZED
```

3. commit only the report/status publication;
4. push directly to `M3`;
5. verify local HEAD = origin/M3 = remote M3 and clean working tree;
6. rerun bounded lifecycle/integrity checks on exact remote HEAD.

The publication commit must not change `docs/architecture/` or executable/test semantics.

If owner corrections were required, they must already be inside `AUDITED_ASIS_SHA` and individually traced to closed findings.

---

# 14. Handoff

Report at minimum:

```text
branch
starting authorization/prompt baselines
AUDITED_ASIS_SHA
publication HEAD
local/origin/remote equality
working-tree state
PR state
changed current owners, if any
CC-01..CC-15 disposition
findings registry
15-file owner hash census
link/hygiene/history-isolation results
41/15/861/21/83/15/63/1/22/12/63/8/8/23 censuses
trusted-read / 22 statement / T3 / cursor / parent-null / Location results
schema/Alembic/non-drift results
build/static/artifact results
PostgreSQL/concurrency results
non-PG/full-suite counts
skip/xfail/rerun/warning census
production/test/schema/dependency changes = none
```

Maximum success claim:

```text
M3 CONSISTENCY CLOSURE — CANDIDATE READY FOR REVIEW
```

Do not claim `COMPLETED`, `DELIVERED`, merged, released or tagged.
