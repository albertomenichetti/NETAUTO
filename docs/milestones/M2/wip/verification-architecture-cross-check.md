# M2 Verification Architecture Cross-Check

**Status:** PASS — VERIFICATION DESIGN COMPLETE — DEPENDENT-OWNER REVIEW / IMPLEMENTATION EVIDENCE PENDING

**Authority:** REVIEW EVIDENCE — NON-NORMATIVE

## Review target

```text
docs/milestones/M2/architecture/verification.md
```

The review compares the verification design with:

```text
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md
docs/general/technology_baseline.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/relationship.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/concurrency-matrix.md
docs/milestones/M2/architecture/concurrency.md

docs/milestones/M2/wip/health-api.md
docs/milestones/M2/wip/netauto-cli.md
docs/milestones/M2/wip/runtime-configuration-production-deployment.md

current test organization and M1 traceability registry on branch M2
```

## Closure summary

```text
M2 outcomes mapped                         PASS — 16/16
acceptance criteria mapped                 PASS — 32/32
stable evidence bundles                    PASS — 32/32
delivered concurrency scenarios preserved  PASS — 51/51
new M2 scenarios registered                PASS — 32/32
canonical M2 scenario census               PASS — 83/83
semantic predicates covered                PASS — 21/21
mutation/matrix consumption                PASS — 41 mutations / 861 cells
verification layers                        PASS — T0 ... T10
AS-IS delta allowlist                       PASS
negative-surface registry                  PASS
schema/migration/startup design            PASS
Health evidence design                     PASS
CLI evidence design                        PASS
packaging/Linux/trust evidence design       PASS
traceability closure                       PASS
open verification-design point             0
implementation evidence                    PENDING by governance
contract reopening                         NOT REQUIRED
```

## Material finding — verification gate circularity

The review found a governance contradiction in the draft architecture wording:

```text
implementation is not authorized until architecture is frozen
while
some draft freeze clauses appeared to require executed M2 implementation
or real-PostgreSQL evidence before architecture freeze
```

That state would make implementation authorization impossible.

The verification owner closes the contradiction through three separate gates:

```text
architecture freeze
    -> complete scenario/evidence design and traceability

implementation-slice completion
    -> affected evidence targets implemented and passing

final delivery
    -> every bundle and canonical scenario executed and PASS
```

This clarification does not weaken any contract criterion. It makes the required evidence executable in the correct governance phase.

`architecture/README.md` is updated as the set-level freeze authority. Any earlier draft phrase such as “verification supplies deterministic evidence” is interpreted at architecture freeze as complete evidence assignment/design; actual execution remains mandatory for slice and delivery gates.

## Scenario-registry result

The delivered registry remains the base:

```text
ROW      17
ARB       7
REF       6
GATE      6
SNAP      4
ATOMIC    4
PAR       7
         --
total    51
```

M2 adds:

```text
ROW-18 ... ROW-30       13
ARB-08                    1
REF-07 ... REF-11         5
GATE-07                   1
SNAP-05                   1
ATOMIC-05 ... ATOMIC-07   3
PAR-08 ... PAR-09         2
PLAN-01 ... PLAN-06       6
                         --
new total                32
```

Final census:

```text
ROW       30
ARB        8
REF       11
GATE       7
SNAP       5
ATOMIC     7
PAR        9
PLAN       6
          --
total     83
```

Modified delivered obligations are limited to frozen M2 deltas:

```text
ARB-05
    collision loser -> relationship_fact_conflict

ARB-06
    same-ID delete waiter -> resource_not_found / 404

ARB-07
    winner-current classification -> conflict, not convergence

SNAP-01 / SNAP-02
    expanded to DATA_CHANGE and SCHEMA_CHANGE real transitions
```

## Predicate coverage

```text
delivered predicates  19/19 preserved
new predicates         VH, RS
final predicates       21/21 mapped
```

`VH` is evidenced by distinct ObjectTemplate/RDV publication races.

`RS` is evidenced by DATA_CHANGE/DATA_CHANGE, DATA_CHANGE/SCHEMA_CHANGE, SCHEMA_CHANGE/SCHEMA_CHANGE, mutation/DELETE and atomic rollback scenarios.

Every canonical T3 scenario treats SQLSTATE `40P01` as failure. There is no retry-based deadlock normalization.

## Acceptance evidence design

The registry uses a one-to-one stable bundle key:

```text
M2-AC-01 -> M2-VER-01
...
M2-AC-32 -> M2-VER-32
```

Each bundle defines:

```text
required test layers
observable assertions
PostgreSQL/concurrency scenarios where applicable
negative assertions
delivery completion condition
```

This permits implementation test names to evolve while contract-level evidence identity remains stable.

## Layer cross-check

The delivered T0–T7 layers are preserved.

M2 adds:

```text
T8
    CLI terminal/client/process

T9
    installed wheel and Linux operating baseline

T10
    static traceability, negative surface and documentation policy
```

The additions do not duplicate existing API, migration or concurrency layers.

## Toolchain and environment cross-check

The design aligns with ratified `STACK-07` and `STACK-08`:

```text
pytest / pytest-asyncio
HTTPX + ASGITransport
real PostgreSQL through TEST_DATABASE_URL
no SQLite fallback
deterministic sessions and pg_blocking_pids()
Hypothesis selectively
pytest-timeout as hang guard
uv locked environment
Ruff and Pyright strict
```

T9 uses the built wheel outside the repository checkout. No Docker/Testcontainers requirement is introduced.

## Contract and architecture traceability

```text
M2-OUT-01 ... M2-OUT-16
    -> architecture owners
    -> M2-AC-*
    -> M2-VER-*
    -> concrete targets

concurrency-matrix predicates
    -> canonical scenarios
    -> recipes
    -> PostgreSQL mechanism
    -> concrete targets

AS-IS guarantees
    -> preserved scenario/test coverage
    -> explicit M2 delta allowlist
```

No outcome, acceptance criterion or predicate is orphaned.

## Dependent-owner handoff

Before `verification.md` can freeze, the following owners must confirm implementation-facing hooks:

```text
health.md
    active query, timeout and safe-message seam

cli.md
    parser/state/transport/PTY and exact operation-map seam

runtime-deployment.md
    installed wheel, migration-resource, startup and process seam
```

These owners may refine how evidence is implemented but may not reduce the stable bundles or acceptance assertions.

## Implementation evidence boundary

No M2 implementation code was added or executed by this documentation task.

The review therefore does not claim:

```text
new lock planner implemented
new M2 tests already passing
new wheel already installable
Health/CLI/runtime implementation already present
```

It claims that the complete required evidence is now designed, classified and traceable.

## Final result

```text
verification architecture       COMPLETE
contract compatibility          PASS
AS-IS compatibility             PASS
concurrency/persistence mapping PASS
governance gate model           PASS
architecture freeze input       READY FOR DEPENDENT-OWNER REVIEW
implementation evidence         PENDING
contract reopening              NOT REQUIRED
```
