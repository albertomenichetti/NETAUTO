# Roadmap

## Current Milestone State

```text
M1 — Functional Core                     COMPLETE

M2 — Hardening current model             COMPLETE
     relational integrity
     lifecycle hardening
     model-plane serialization
     data-plane concurrency characterization
     Object optimistic concurrency
     ownership graph coordination
     fail-closed concurrency composition

M3 — Real-world dogfooding               NEXT
     First Real NETAUTO Network Model
     likely starting domain:
       Site
       Device
       Interface
       VLAN
       IP Address

M4 — Candidate Data-Model Freeze         FUTURE

M5 — Integrity Verifier                  DEFERRED UNTIL FREEZE

M6 — Destructive/adversarial certification
                                          DEFERRED

M7 — Alembic + PostgreSQL                DEFERRED

M8 — Expansion                           FUTURE / guided by dogfooding
```

## Agreed Order

The current agreed order is:

```text
dogfooding
-> model evolution
-> candidate model freeze
-> integrity verifier
-> destructive certification
-> Alembic/PostgreSQL
```

This order is deliberate. The current implementation is already strong enough
to start learning from a real network-domain model before freezing persistence
and backend-evolution choices too early.

## M3 — Real-World Dogfooding

The next step is not speculative feature growth in the abstract. It is using
the existing platform to model a real NETAUTO domain and learning where the
current model is strong, awkward, or insufficient.

The likely first dogfood domain is:

- `Site`
- `Device`
- `Interface`
- `VLAN`
- `IP Address`

Dogfooding findings should be classified as:

- `A. model cannot express the case`
- `B. model can express it but unnaturally`
- `C. model is adequate but application/API/CLI ergonomics are poor`

This distinction matters. A model gap, an awkward modeling pattern, and an
ergonomic issue should not be treated as the same kind of future work.

## M4 — Candidate Data-Model Freeze

After real dogfooding and resulting model evolution, the project can define a
candidate freeze for the structural model and its invariants.

That freeze is the prerequisite for later integrity-verifier and adversarial
hardening work.

## M5 — Integrity Verifier

The integrity verifier remains intentionally deferred until after the candidate
model freeze. It should verify the model that the project actually intends to
stabilize, rather than a still-moving target.

## M6 — Destructive / Adversarial Certification

Destructive and adversarial persistence certification is also deferred until
the model is stable enough that the certification target is worth locking
down.

## M7 — Alembic And PostgreSQL

SQLite remains the only implemented SQL backend today.

PostgreSQL and Alembic are deferred, not abandoned. They are intentionally
sequenced after:

- real dogfooding
- model evolution
- candidate freeze
- integrity verification direction

That avoids prematurely freezing migration and cross-backend assumptions around
an immature model.

## M8 — Expansion

Further platform expansion remains future work guided by dogfooding and the
actual needs discovered there.

Speculative ideas such as component cardinality, relationship cardinality,
natural keys, tags, relationship attributes, ordered components, or bulk
operations are not committed roadmap items today. They remain possible
discoveries, not current promises.
