# M2 final-acceptance evidence record format

This directory contains non-normative evidence-format guidance beneath the frozen M2 verification architecture. It does not add product, architecture, or acceptance semantics.

M2-S08 defines and tests the finite record shape only. S08 does not create or populate a candidate-specific evidence record. M2-S09 owns creation of that record for one exact candidate commit and the reviewer owns the final `reviewer_decision`. Validation has two explicit phases: the implementer phase requires that field to remain null; the reviewer phase requires exactly `ACCEPTED` or `REVIEW CHANGES REQUIRED`.

## Representation

The record is serialized as UTF-8 JSON with lexicographically sorted object keys, compact separators, and one final newline. Sets are represented as objects keyed by their stable identifier so missing and extra identifiers remain reviewable. Command argument vectors are arrays of separate strings; they are evidence, not shell source.

The test-only dataclasses and validator in `tests/support/m2_evidence.py` are the executable format authority. The record uses schema version `1` and contains these required top-level fields:

```text
schema_version
candidate_commit
branch
release_version
wheel
runtime_lock
environment
locked_environment_confirmed
build_confirmed
commands
evidence_bundles
scenarios
predicates
schema
operations
installed_t9
runtime_census
open_findings
reviewer_decision
```

## Required content

`candidate_commit` is a lowercase 40-hex Git SHA and `branch` is `M2`. `wheel` records filename/path, byte size, member count, and a lowercase 64-hex SHA-256. `runtime_lock` records the embedded lock source path `src/netauto/release/runtime.pylock.toml`, byte size, package count, and its lowercase 64-hex SHA-256.

`environment` records the effective CPython, uv, Hatchling, PostgreSQL, and Linux versions. The locked-environment and build confirmations are explicit booleans.

Every command ledger item records the exact `argv`, exit status, duration in seconds, and its selected, passed, skipped, xfailed, rerun, and warning census. Durations and all counts are non-negative.

The stable ledgers are exact and admit neither missing nor extra keys:

```text
evidence_bundles    M2-VER-01 ... M2-VER-32
scenarios           the canonical 83 scenario identifiers
predicates          the canonical 21 safety predicates
```

Every ledger value uses the frozen vocabulary:

```text
DESIGNED
IMPLEMENTED
PASS
FAIL
BLOCKED
```

The `schema` object records the 15-table census, one Alembic base/head, the actual database revision, and the `compare_metadata` result. A passing result has base, head, and actual revision equal to `0001_m2_kernel` and an empty `compare_metadata` array.

The `operations` object records the exact business HTTP, Health HTTP, remote CLI, local CLI, and CLI-example censuses. The frozen values are `63`, `1`, `63`, `8`, and `65` respectively. `installed_t9` records the installed-wheel gate state.

`runtime_census` records skip, xfail, rerun, warning, supported-path `40P01`, and unexpected `40001` counts. `open_findings` is an explicit array, including the empty case.

## Safety and ownership

The record contains no database URL, DSN, URL userinfo, credential, password, token, private key, secret field, or secret-bearing value. HTTP and HTTPS endpoint values are permitted only when they contain no userinfo. Artifact hashes identify evidence without embedding artifacts or sensitive configuration.

`reviewer_decision` is reserved for reviewer ownership. It remains null when validated in implementer phase and cannot be pre-populated as accepted, completed, delivered, or any equivalent decision. During reviewer-phase validation it must contain exactly one finite reviewer outcome: `ACCEPTED` or `REVIEW CHANGES REQUIRED`. The S09 implementer record reports evidence for inspection; it does not approve itself.
