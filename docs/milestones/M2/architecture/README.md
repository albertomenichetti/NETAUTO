# M2 Architecture

**Architecture set status:** DESIGN NOT STARTED — NOT FROZEN

## Purpose and authority boundary

This directory will contain the normative M2 TO-BE architecture required to satisfy `../contract.md`.

Authority is combined as follows:

```text
current delivered AS-IS in docs/architecture/
+
explicit frozen M2 architecture delta
=
implementation authority for M2
```

This README controls the composition and set-level status of the M2 architecture corpus. Detailed decisions belong to the owning documents indexed here and must not be duplicated in this file.

## Current baseline

The starting architecture is the delivered AS-IS under:

```text
docs/architecture/
```

No M2-specific architectural change has been defined yet.

## Normative document map

No M2 architecture documents are registered yet.

| Area | Owning document | Status |
|---|---|---|
| M2 TO-BE | TBD after contract definition | NOT STARTED |

## Coverage and ownership map

TBD after the M2 contract is sufficiently defined to identify every affected semantic and technical area.

## Open design points

- M2 contract is not frozen.
- M2 TO-BE scope and owning architecture documents are not yet identified.
- No architecture decision is ready for implementation.

## Freeze condition

The architecture set may become `FROZEN` only when:

- `../contract.md` is `FINAL / FROZEN`;
- every contract area has an explicit owning architecture document;
- all required semantic, persistence, concurrency, API, failure and verification decisions are closed;
- cross-document consequences are propagated;
- no relevant open or partially reopened point remains;
- the complete set has passed a consistency sweep.

Until then, implementation of M2 behavior is not authorized.
