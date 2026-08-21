# M2 — AS-IS consolidation verification amendment

**Status:** FINAL — reviewer-owned amendment to `as-is-consolidation.md`.

## Purpose and precedence

This document amends only the verification-transition boundary of:

```text
docs/milestones/M2/as-is-consolidation.md
```

All semantic, writing, ownership, source-corpus, target-corpus, publication and
delivery rules in the owning consolidation specification remain unchanged.

This amendment exists because one permanent M2 regression test currently treats
`docs/architecture/` as the pre-M2 delivered baseline. During consolidation that
same directory becomes the authoritative current AS-IS. It cannot simultaneously
serve as the historical left-hand side of an M2 delta comparison and as the
current post-M2 architecture.

The finding is a verification-harness transition defect. It is not a product,
architecture, schema, API or consolidation-content contradiction.

## Observed blocking gate

The exact blocking target is:

```text
tests/test_m2_s08_regression.py::
    test_public_route_error_and_schema_runtime_deltas_are_exact
```

Its pre-consolidation assertions currently require:

```text
docs/architecture/api.md                   52 business operations
docs/architecture/persistence.md           the historical 13-table set
```

The accepted current system and the consolidation gate require instead:

```text
current business operations                63
current operational HTTP routes            GET /health/core only
current PostgreSQL tables                   15
current Alembic base/head/current authority 0001_m2_kernel
```

Keeping the old assertions would make a correct current AS-IS impossible.
Removing or hiding the eleven current routes from the documentation parser, or
omitting the two current tables, would weaken the gate and falsify the AS-IS.

## Narrow scope authorization

The consolidation candidate may additionally modify exactly:

```text
tests/test_m2_s08_regression.py
```

No other test file is authorized by this amendment.

The complete candidate delta is therefore limited to:

```text
docs/architecture/*.md
docs/milestones/M2/status.md
tests/test_m2_s08_regression.py
```

The four current AS-IS files already authorized for creation remain:

```text
docs/architecture/health.md
docs/architecture/cli.md
docs/architecture/runtime-deployment.md
docs/architecture/linux-operating-baseline.md
```

All original prohibitions remain in force for:

```text
src/netauto/
all other tests
schema and migrations
pyproject.toml
uv.lock
src/netauto/release/runtime.pylock.toml
README.md root
AGENTS.md
docs/general/
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/
docs/milestones/M2/steps.md
docs/milestones/M2/acceptance.md
docs/milestones/M2/evidence/
```

If another test fails because it also treats `docs/architecture/` as the
historical pre-M2 baseline, stop and report its exact node and assertion. This
amendment is not a generic permission to rewrite tests reactively.

## Required test transition

Keep the existing pytest node identity:

```text
tests/test_m2_s08_regression.py::
    test_public_route_error_and_schema_runtime_deltas_are_exact
```

The stable node is already part of the permanent M2 verification registries. Do
not rename or remove it unless a separate reviewer-owned amendment changes that
registry.

Rewrite the target so that it verifies the current AS-IS against current finite
authorities, while preserving historical M2 delta registries as historical
closure evidence.

### Current API assertions

The test must establish at least:

```text
documented current business operations == BUSINESS_OPERATION_SET
business operation count                 == 63
M2 frozen business inventory             == BUSINESS_OPERATION_SET
GET /health/core                          excluded from business inventory
PUBLIC_HTTP_OPERATIONS                    == BUSINESS_OPERATION_SET + Health
complete public HTTP operation count      == 64
public error-code count                   == 23
```

Path-parameter names may be normalized only to compare semantically identical
route templates. The documentation must still contain the exact human-readable
current route inventory.

The historical route delta registries remain exact:

```text
S01_PUBLIC_ROUTE_DELTA                    9
S02_PUBLIC_ROUTE_DELTA                    2
combined historical business delta       11
S04_PUBLIC_ROUTE_DELTA                    GET /health/core
```

They may be checked against the frozen milestone registry or the current
business registry. They must not use `docs/architecture/api.md` as a fabricated
52-route pre-M2 snapshot after consolidation.

Forbidden approaches include:

```text
filtering the eleven routes out of the AS-IS parser
maintaining a hidden second route list in docs/architecture
loosening equality to minimum counts
counting Health as a business operation
using the historical milestone document as current authority
```

### Current persistence assertions

The test must establish at least:

```text
documented current table inventory        == EXPECTED_TABLES
current documented table count             == 15
set(metadata.tables)                       == EXPECTED_TABLES
migration file inventory                   == 0001_m2_durable_kernel.py
migration revision                         == 0001_m2_kernel
migration down_revision                    == null
```

The current documented inventory is exactly:

```text
datatypes
datatype_versions
object_templates
object_template_versions
object_template_properties
object_template_components
relationship_definitions
relationship_resolutions
relationship_definition_versions
relationship_definition_properties
objects
object_components
relationships
runtime_relationship_resolutions
object_lifecycle_events
```

Use an exact, finite documentation-inventory parser or an equivalently strong
assertion. Loose substring checks that can pass with extra or missing tables are
not sufficient.

The historical 13-table predecessor may remain represented inside historical
M2 delta registries or cycle history. It must not be required from the current
`docs/architecture/persistence.md`.

### Historical closure preservation

Do not weaken or remove:

```text
M2_DELTA_ALLOWLIST
M2_PUBLIC_WIRE_DELTA_ALLOWLIST
M2_SCHEMA_RUNTIME_DELTA_ALLOWLIST
M2_DELIVERED_SCENARIO_DELTA_ALLOWLIST
S01_PUBLIC_ROUTE_DELTA
S02_PUBLIC_ROUTE_DELTA
S04_PUBLIC_ROUTE_DELTA
```

The distinction is:

```text
historical M2 registries
    -> prove the accepted milestone delta remained exact

current docs/architecture
    -> prove the complete system state that exists now
```

The current AS-IS must never be made historical merely to keep a pre-delivery
assertion green.

## Development and verification sequence

Continue from the existing dirty consolidation worktree. Do not reset, stash,
rebase, discard or recreate the fifteen-document draft.

Before integrating this amendment, verify that the local worktree does not
modify:

```text
docs/milestones/M2/as-is-consolidation-verification-amendment.md
```

Then fetch and fast-forward to the current `origin/M2`. The reviewer commit adds
only this non-overlapping amendment file. If Git cannot fast-forward without
overwriting local work, stop and report; do not force the update.

After the test transition, execute first:

```text
tests/test_m2_s08_regression.py::
    test_public_route_error_and_schema_runtime_deltas_are_exact

all tests in tests/test_m2_s08_regression.py
traceability and documentation-policy focused tests
```

Then execute every audit and repository gate required by
`as-is-consolidation.md`, including PostgreSQL/concurrency, non-PostgreSQL and the
full repository suite.

Required outcomes remain:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATE        exact expected census
compare_metadata                 []
new unexplained warnings         0
artifact identity                unchanged
```

No retry, deselection, count weakening or test deletion is permitted.

## Commit and publication boundary

Use a bounded commit split, preferably:

```text
test(m2): align AS-IS regression gate with current authority
docs(architecture): consolidate current AS-IS
docs(m2): publish AS-IS consolidation candidate
```

The test-only transition commit must contain only:

```text
tests/test_m2_s08_regression.py
```

Do not use `git add .`, `git add -A` or `git add --all`.

If all exact-remote gates pass, the only implementer handoff remains:

```text
AS-IS consolidation    CANDIDATE READY FOR REVIEW
consistency closure    BLOCKED
M2                     NOT DELIVERED
```

The coding agent must not mark the consolidation `COMPLETED`, open the
consistency-closure gate, declare M2 `DELIVERED` or merge.