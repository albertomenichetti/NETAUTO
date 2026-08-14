# M1 — PostgreSQL Concurrency Realization: Relationship model/runtime

**Status:** DRAFT — REALIZE-12 ratificato; il documento viene esteso con i successivi predicate Relationship.

Companion di `concurrency-postgresql-realization-matrix.md`. La catena normativa resta:

```text
semantic predicate
-> concurrency authority
-> physical authority
-> PostgreSQL mechanism
-> loser/retry behavior
-> real PostgreSQL concurrency test
```

---

## 1. REALIZE-12 — `S-RD-CERTIFIED-SET` (`RC`)

La authority è il current committed certified `RelationshipDefinition` set, composto da Definition headers + complete authoritative Resolution sets. La stable ObjectTemplate lineage ancestry partecipa alla semantica di endpoint-space overlap.

Il mechanism è l'exclusive transaction-level advisory lock:

```text
RELATIONSHIP_DEFINITION_CONFLICT_GATE
```

acquisito da `RD.CREATE` e `RD.RENAME`, non da `RD.DELETE`.

### 1.1 Fresh-snapshot rule dopo il gate

Gate acquisition e authoritative certified-set read sono sempre SQL statement separati:

```text
statement 1:
    SELECT pg_advisory_xact_lock(...)

statement 2+:
    read/re-read protected certified set
```

A `READ COMMITTED` questo garantisce che un waiter osservi con un nuovo snapshot lo state committed dal precedente gate holder. Il gate stabilizza i writer; non è esso stesso l'authority del certified set.

### 1.2 `RD.CREATE`

```text
local complete-candidate validation
-> acquire conflict gate
-> fresh certified-set read
-> semantic-equivalence check
-> global cross-Definition Resolution conflict check
-> insert Definition + complete Resolution set
-> commit while holding gate
```

Equivalence e conflict appartengono alla stessa protected critical section. Una sola Resolution conflicting fa fallire l'intera candidate Definition.

### 1.3 `RD.RENAME`

```text
Definition header FOR UPDATE
-> load/re-read own complete aggregate
-> acquire conflict gate
-> fresh certified-set read
-> derive final renamed complete candidate
-> equivalence/conflict check excluding self
-> atomically update the complete relevant Resolution-name set
-> commit while holding gate
```

Same-Definition rename/delete lifetime resta serializzata dalla Definition header, non dal global gate.

### 1.4 `RD.DELETE`

`RD.DELETE` non acquisisce il conflict gate perché può soltanto rimuovere un blocker dal certified set. Se CREATE/RENAME vede ancora il blocker prima che la delete committi, una conservative semantic failure è valida; se la delete è già committed quando il gate holder fa il fresh read, la candidate può diventare ammissibile.

### 1.5 No fan-out locks / no runtime gate

Il protected global check non prende `FOR UPDATE` su tutte le altre Definition rows: il gate serializza le sole supported predicate-changing mutation `CREATE/RENAME`.

Runtime `Relationship.CREATE/DELETE` non acquisisce il conflict gate: consumano un Definition contract già certified. Endpoint ObjectTemplate lineage lifetime resta `S-REFERENCE-LIFETIME` con FK `RESTRICT`, non `RC`.

M1 non introduce ancestry-closure authority né partitioned/name-keyed conflict gates.

### 1.6 Gate lifetime

`RELATIONSHIP_DEFINITION_CONFLICT_GATE` è `pg_advisory_xact_lock` e resta detenuto fino a commit/rollback. Rilasciarlo prima del commit permetterebbe a un altro candidate di validare contro uno state precedente non ancora visibile.

### 1.7 Required PostgreSQL tests

Almeno:

1. equivalent concurrent `RD.CREATE × RD.CREATE` -> un solo certified Definition;
2. non-equivalent but conflicting concurrent CREATE -> un solo winner;
3. unrelated CREATE -> correctness con intentional global over-serialization;
4. `RD.CREATE × RD.RENAME` che diventano conflicting;
5. `RD.RENAME(D1) × RD.RENAME(D2)` verso conflicting state;
6. same-Definition rename × rename -> Definition-header serialization prima del gate;
7. non-symmetric/symmetric complete rename atomicity;
8. waiter vede lo state committed dal previous gate holder;
9. explicit fresh-snapshot-after-advisory-wait test;
10. global check senza fan-out `FOR UPDATE` sulle Definition;
11. blocker `RD.DELETE × CREATE/RENAME`, entrambi gli scheduling ammessi;
12. endpoint OT lineage DELETE vs RD.CREATE -> FK lifetime arbitration;
13. rollback CREATE/RENAME non lascia partial certified candidate;
14. gate held through commit;
15. runtime Relationship mutation non prende il conflict gate;
16. endpoint overlap test per equality/ancestor/descendant.
