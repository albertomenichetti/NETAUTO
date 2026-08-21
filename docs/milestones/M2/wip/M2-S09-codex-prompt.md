# Codex review-fix prompt — M2-S09 final harness closure

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

Questo file sostituisce il precedente aid S09 nello stesso path e autorizza
esclusivamente la continuazione correttiva di:

```text
M2-S09 — Full M2 acceptance and delivery-candidate gate
```

Il lavoro è limitato ai finding reviewer-owned:

```text
S09-RF-01 — reviewer lifecycle coherence
S09-RF-02 — fail-closed final-gate runner
```

Il prompt è subordinato a `AGENTS.md`, al current AS-IS consegnato, al contract
e all’architecture set M2 `FINAL / FROZEN`, a `steps.md`, alla technology
baseline ratificata e soprattutto allo stato reviewer-owned in `status.md`.
Non crea semantica, non riapre l’architettura e non autorizza capability o
correzioni di produzione.

---

## 1. Repository, branch e ancestry

Lavora direttamente su:

```text
repository   albertomenichetti/NETAUTO
branch       M2
```

Reviewer-owned starting baseline obbligatoria nell’ancestry:

```text
2afc3eb1d86bb829185981279d8c6fe9a1667b11
docs(m2): reject S09 candidate for harness closure
```

Preserva inoltre integralmente nell’ancestry:

```text
95a61e0815472e85be55828fa546e916c0cb3e66
98405300ffd009a96ba187c8e5fe6f93d489303e
b0546b1109c66a57195c50294291cb4a32ad48f2
0b1de73487061f68ed96ef78f48ad67866f11867
c8e4fc04874da6ef28d80115bd6c4d7aaeb4441f
2afc3eb1d86bb829185981279d8c6fe9a1667b11
```

La SHA che pubblica questo aid è necessariamente successiva a `2afc3eb...`.
Dopo `git pull --ff-only`, usa l’esatto `origin/M2` corrente come starting HEAD.
Non tornare a una SHA precedente.

Non eseguire:

```text
reset
rebase
force-push
history rewrite
merge su master
```

---

## 2. Mandatory pre-flight

Prima di modificare file verifica:

```text
git branch --show-current                  M2
git pull --ff-only                         successo / già aggiornato
HEAD == origin/M2                          sì
working tree                               pulito
origin/M2 contiene 2afc3eb...              sì
questo aid esiste all’HEAD                 sì
M2-S00 ... M2-S08                          COMPLETED
M2-S09                                     REVIEW CHANGES REQUIRED
M2                                         NOT DELIVERED
contract                                   FINAL / FROZEN
architecture set                           FINAL / FROZEN
steps                                      FINAL / FROZEN
reopen architetturali aperti               nessuno
```

Verifica inoltre, prima di alterare il lifecycle corrente, che siano presenti:

```text
docs/milestones/M2/evidence/
    candidate-b0546b1109c66a57195c50294291cb4a32ad48f2.json

docs/milestones/M2/acceptance.md
```

Il record rifiutato deve contenere:

```text
candidate_commit       b0546b1109c66a57195c50294291cb4a32ad48f2
reviewer_decision      REVIEW CHANGES REQUIRED
open_findings          S09-RF-01 e S09-RF-02
```

Non riscrivere la decisione reviewer-owned. La sua rimozione dal working tree è
ammessa soltanto più avanti, quando il nuovo ciclo viene portato a
`IN PROGRESS`; la decisione resta preservata nella cronologia Git.

Se status, record, acceptance summary o ancestry non concordano, fermati senza
modificare il repository.

### 2.1 PostgreSQL

La correzione focused può essere sviluppata senza I/O PostgreSQL, ma un nuovo
candidate S09 non può essere congelato o consegnato senza `TEST_DATABASE_URL`.

Il target può usare hostname locale o loopback. Deve però:

```text
usare postgresql+psycopg
raggiungere PostgreSQL reale
essere fornito e gestito fuori dal test process NETAUTO
identificare il database di test dedicato richiesto dai safety check
non usare SQLite, fake, embedded DB, Docker o Testcontainers
non usare fallback silenzioso
```

Prima del full gate esegui un probe bounded e registra senza credenziali:

```text
versione PostgreSQL
identità del database
SELECT 1
```

Non stampare o committare URL, DSN, user, password o secret.

---

## 3. Authority da rileggere

Rileggi almeno:

```text
README.md
AGENTS.md
docs/general/linee_guida_progetto.md
docs/general/technology_baseline.md

docs/architecture/README.md
docs/architecture/verification.md
docs/architecture/verification-concurrency-registry.md

docs/milestones/M2/contract.md
docs/milestones/M2/architecture/README.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/concurrency.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/architecture/api.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

docs/milestones/M2/evidence/README.md
docs/milestones/M2/acceptance.md
docs/milestones/M2/wip/M2-S09-codex-prompt.md
```

Ispeziona almeno:

```text
tests/support/m2_evidence.py
tests/support/s09_acceptance.py
tests/test_m2_s09_acceptance.py
tests/test_m2_s08_evidence.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_traceability.py
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
```

Il presente aid non è semantic authority. In caso di conflitto prevalgono le
authority frozen e `status.md`.

---

## 4. Scope autorizzato

La correzione è esclusivamente test/evidence/documentation-only.

File modificabili quando necessari:

```text
tests/support/s09_acceptance.py
tests/test_m2_s09_acceptance.py
tests/test_m2_s08_evidence.py
tests/test_m2_s08_negative_surface.py

docs/milestones/M2/evidence/README.md
docs/milestones/M2/evidence/candidate-*.json
    soltanto rimozione del record rifiutato e creazione del nuovo record

docs/milestones/M2/acceptance.md
    rimozione del summary rifiutato e creazione del nuovo summary
docs/milestones/M2/status.md
```

Non modificare:

```text
src/netauto/
public API / DTO / error catalog
CLI grammar, registry, rendering o terminal behavior
Health contract
SQLAlchemy metadata
schema / DDL / indici
migration 0001_m2_kernel o Alembic graph
pyproject dependencies
uv.lock
src/netauto/release/runtime.pylock.toml
versione 0.2.0
wheel content
tests/support/m2_evidence.py
frozen contract / architecture / steps
```

Non creare:

```text
nuova capability
nuova route o command
nuova tabella, migration o setting
auth o server-side TLS
Docker / Kubernetes / systemd product
GitHub Actions
PR
tag
GitHub Release
artifact publication
AS-IS consolidation
merge
```

Un finding di produzione interrompe S09 e deve essere restituito alla slice
proprietaria o al formale processo di architecture reopen. Non correggerlo
silenziosamente dentro il final gate.

---

# 5. S09-RF-01 — Reviewer lifecycle coherence

## 5.1 Stato finito esatto

Estendi `S09State` e `s09_state()` affinché il vocabolario ammesso sia
esattamente:

```text
READY
IN PROGRESS
CANDIDATE READY FOR REVIEW
REVIEW CHANGES REQUIRED
COMPLETED
```

Qualunque altro valore deve produrre un errore deterministico e bounded.

Non usare substring, prefix match o fallback impliciti.

## 5.2 Matrice stato / record / decisione / summary / aid

Implementa e verifica la seguente matrice esatta.

```text
READY / IN PROGRESS
    candidate record        assente
    acceptance.md           assente
    reviewer_decision       non applicabile
    active S09 aid          presente

CANDIDATE READY FOR REVIEW
    candidate record        esattamente uno
    acceptance.md           presente
    reviewer_decision       null
    validation phase        implementer
    record ledgers          tutti PASS
    installed_t9            PASS
    open_findings           vuoto
    active S09 aid          presente

REVIEW CHANGES REQUIRED
    candidate record        esattamente uno
    acceptance.md           presente
    reviewer_decision       REVIEW CHANGES REQUIRED
    validation phase        reviewer
    record ledgers          possono essere PASS / FAIL / BLOCKED
    open_findings           può essere non vuoto
    active S09 aid          presente

COMPLETED
    candidate record        esattamente uno
    acceptance.md           presente
    reviewer_decision       ACCEPTED
    validation phase        reviewer
    record ledgers          tutti PASS
    installed_t9            PASS
    open_findings           vuoto
    active S09 aid          assente
```

`REVIEW CHANGES REQUIRED` non implica che debba esistere un runtime failure:
il reviewer può rifiutare un candidate per un finding qualitativo o di harness.

## 5.3 Coerenza della decisione

Introduci una helper test-only unica, o un meccanismo equivalente, che le prove
S08/S09 possano usare per applicare la matrice senza duplicare branch
inconsistenti.

Comportamento obbligatorio:

```text
CANDIDATE READY FOR REVIEW + null
    valido

REVIEW CHANGES REQUIRED + REVIEW CHANGES REQUIRED
    valido

COMPLETED + ACCEPTED
    valido

CANDIDATE READY FOR REVIEW + decisione valorizzata
    invalido

REVIEW CHANGES REQUIRED + null
    invalido

REVIEW CHANGES REQUIRED + ACCEPTED
    invalido

COMPLETED + null
    invalido

COMPLETED + REVIEW CHANGES REQUIRED
    invalido
```

Continua a usare:

```text
validate_evidence_record(..., phase="implementer")
validate_evidence_record(..., phase="reviewer")
```

Non indebolire il validator S08 e non modificare il vocabolario
`REVIEWER_DECISIONS`.

## 5.4 Acceptance summary phase-aware

La verifica di `acceptance.md` non deve più richiedere wording candidate in
tutti gli stati reviewer.

Usa marker finiti e specifici per fase.

### Candidate

```text
# M2 Final Acceptance Candidate
Status: CANDIDATE READY FOR REVIEW
reviewer decision PENDING / reviewer-owned
M2-S09 is not COMPLETED
M2 is not DELIVERED
```

### Review changes required

```text
# M2 Final Acceptance Review
Status: REVIEW CHANGES REQUIRED
reviewer decision REVIEW CHANGES REQUIRED
M2-S09 REVIEW CHANGES REQUIRED
M2 NOT DELIVERED
```

### Completed

```text
# M2 Final Acceptance Review
Status: ACCEPTED
reviewer decision ACCEPTED
M2-S09 COMPLETED
M2 NOT DELIVERED
```

Dopo S09 `COMPLETED`, `M2 NOT DELIVERED` resta corretto finché il successivo
consolidamento AS-IS e la delivery reviewer-owned non sono conclusi.

Il test deve rifiutare summary stale, incluso:

```text
COMPLETED con Status: CANDIDATE READY FOR REVIEW
COMPLETED con "M2-S09 is not COMPLETED"
REVIEW CHANGES REQUIRED con summary candidate/pending
candidate con reviewer decision già valorizzata
```

## 5.5 Evidence inventory

`validate_evidence_lifecycle()` deve accettare anche lo stato
`REVIEW CHANGES REQUIRED` come stato con un singolo record e `acceptance.md`.

Preserva:

```text
un solo README di formato
al massimo un candidate JSON nel working tree
nessun file evidence non classificato
record filename == candidate_commit
candidate SHA antenato dell’evidence HEAD
candidate SHA privo di acceptance.md
```

## 5.6 WIP lifecycle

Il test WIP deve continuare a imporre:

```text
READY
IN PROGRESS
CANDIDATE READY FOR REVIEW
REVIEW CHANGES REQUIRED
    -> M2-S09-codex-prompt.md presente

COMPLETED
    -> M2-S09-codex-prompt.md assente
```

Preserva esattamente:

```text
19 historical WIP disposition rows
2 permanent closure records
0 implementation dependency on WIP
0 unclassified historical document
at most one active execution aid
```

La simulazione della futura rimozione reviewer-owned deve restare verde.

## 5.7 Documentazione evidence

Aggiorna `docs/milestones/M2/evidence/README.md` affinché descriva esplicitamente
anche:

```text
REVIEW CHANGES REQUIRED
    record mantenuto
    decisione reviewer finita
    rejection summary presente
    aid attivo mantenuto

nuovo ciclo IN PROGRESS dopo rejection
    vecchio record e summary ritirati dal working tree
    rejection preservata in Git history
    nuovo candidate futuro con nuova SHA e nuovo unico record
```

## 5.8 Regressioni obbligatorie

Aggiungi o rafforza prove pure e deterministiche per:

```text
exact five-state vocabulary
pre-candidate READY / IN PROGRESS
candidate/null
review-changes-required/correct decision
completed/ACCEPTED
all incoherent state/decision combinations
phase-specific acceptance markers
current reviewer-owned rejection record
future reviewer acceptance state
WIP aid present during rejection
WIP aid absent only after completion
```

La prova reale deve passare inizialmente sullo stato corrente:

```text
M2-S09 REVIEW CHANGES REQUIRED
candidate-b0546... presente
reviewer_decision REVIEW CHANGES REQUIRED
acceptance review summary presente
```

Dopo la successiva transizione a `IN PROGRESS`, la stessa suite deve passare con
record e `acceptance.md` assenti.

---

# 6. S09-RF-02 — Fail-closed final-gate runner

## 6.1 Exit status effettivo

Introduci una helper pura equivalente a:

```text
gate_exit_status(parsed: ParsedPytestRun) -> int
```

Regole esatte:

```text
raw pytest exit status non-zero
    -> risultato non-zero

qualunque requested target != PASS
    -> risultato non-zero

census.skipped > 0
    -> risultato non-zero

census.xfailed > 0
    -> risultato non-zero

census.rerun > 0
    -> risultato non-zero

raw exit zero + tutti i target PASS + skip/xfail/rerun zero
    -> risultato zero
```

La warning Starlette già censita non deve da sola rendere non-zero il gate.

Un return code negativo da segnale deve essere normalizzato a un valore
non-zero positivo per la command evidence.

## 6.2 XPASS

Il collector corrente riversa gli XPASS summary nel censimento `xfailed`.
Mantieni o rendi più esplicita questa policy, purché:

```text
XPASS osservato -> gate non-zero
```

Non introdurre un successo silenzioso per XPASS.

## 6.3 BLOCKED e JUnit assente

Se:

```text
un requested target non appare nel JUnit
il JUnit non viene prodotto
il node ID concreto non corrisponde al target richiesto
```

quel target resta `BLOCKED` e il comando pubblico deve terminare non-zero.

## 6.4 Output pubblico coerente

`_run_group()` deve usare lo status effettivo, non il solo
`completed.returncode`.

Il JSON stampato deve riportare:

```text
exit_status          status effettivo del comando harness
failed_targets       ogni target non PASS
output_tail          diagnostica bounded quando lo status effettivo è non-zero
```

Puoi aggiungere separatamente:

```text
pytest_exit_status
```

come diagnostica del subprocess sottostante, ma il command ledger deve usare
l’exit status effettivo del comando pubblico:

```text
uv run python -m tests.support.s09_acceptance run bundles
uv run python -m tests.support.s09_acceptance run scenarios
```

## 6.5 Refactor testabile

È raccomandato separare:

```text
esecuzione subprocess/JUnit
calcolo dello status effettivo
costruzione del result object
stampa/return CLI
```

in modo che le regressioni non debbano avviare centinaia di test soltanto per
provare il fail-closed behavior.

Una struttura equivalente è ammessa, purché una prova integri davvero
`_run_group()` o il suo wrapper pubblico e dimostri che lo status derivato viene
restituito.

## 6.6 Regressioni obbligatorie

Copri separatamente:

```text
all targets PASS + raw 0             -> 0
raw pytest non-zero                  -> non-zero
target FAIL + raw 0                  -> non-zero
target BLOCKED + raw 0               -> non-zero
SKIP + raw 0                          -> non-zero
XFAIL + raw 0                         -> non-zero
XPASS summary + raw 0                 -> non-zero
RERUN + raw 0                         -> non-zero
JUnit assente                         -> non-zero
warning nota + tutto PASS             -> 0
```

Verifica inoltre che, nei casi derivati non-zero:

```text
result["exit_status"] sia non-zero
failed_targets sia valorizzato quando pertinente
output_tail sia bounded e disponibile
```

Non aggiungere retry, rerun automatici, sleep o timeout più ampi per ottenere un
passaggio.

---

## 7. Focused review-fix verification nello stato rifiutato

Prima di ritirare il vecchio record, esegui sul tree corretto ma ancora nello
stato reviewer-owned `REVIEW CHANGES REQUIRED` almeno:

```text
tutti i nuovi test S09-RF-01
tutti i nuovi test S09-RF-02
tests/test_m2_s09_acceptance.py completo
tests/test_m2_s08_evidence.py completo
WIP lifecycle target
tests/test_m2_traceability.py
```

Richiedi che il record rifiutato reale venga validato in reviewer phase con:

```text
reviewer_decision = REVIEW CHANGES REQUIRED
```

Non richiedere `open_findings == ()` nello stato rifiutato. Non richiedere che
tutti i ledger siano `PASS` per ogni possibile rejection, anche se il record
corrente li contiene tutti `PASS`.

Commit consigliato:

```text
test(m2): close S09 harness review findings
```

Questo commit può mantenere temporaneamente:

```text
M2-S09 REVIEW CHANGES REQUIRED
vecchio record presente
rejection acceptance.md presente
```

Pusha su `M2` e verifica branch sincronizzato prima di proseguire.

---

## 8. Avvio del nuovo candidate cycle

Dopo che il lifecycle rifiutato è provato:

```text
1. aggiorna status.md a M2-S09 IN PROGRESS;
2. mantieni M2 NOT DELIVERED;
3. elimina dal working tree:
       docs/milestones/M2/evidence/
           candidate-b0546b1109c66a57195c50294291cb4a32ad48f2.json
       docs/milestones/M2/acceptance.md
4. lascia docs/milestones/M2/evidence/README.md;
5. lascia attivo questo execution aid;
6. riesegui le prove lifecycle nello stato IN PROGRESS.
```

La rejection resta preservata nel commit `2afc3eb...` e nell’eventuale commit
focused precedente. Non duplicarla in un secondo record storico nel working
tree.

Commit consigliato:

```text
docs(m2): start replacement S09 candidate cycle
```

Dopo questo commit:

```text
candidate JSON inventory      vuoto
acceptance.md                 assente
M2-S09                        IN PROGRESS
M2                            NOT DELIVERED
```

Pusha e verifica:

```text
HEAD == origin/M2 == remote M2
ahead / behind == 0 / 0
working tree pulito
```

Se non servono altre modifiche, questo esatto commit diventa il nuovo
`CANDIDATE_SHA`. Se correggi ancora il solo harness, committa e pusha prima di
congelare la SHA definitiva.

---

## 9. Nuovo candidate SHA e full gate da zero

Non riutilizzare:

```text
candidate SHA b0546b1...
vecchio candidate JSON
vecchi command ledger
vecchie durate
vecchi JUnit XML
vecchi artifact
```

Congela il nuovo candidate soltanto quando contiene:

```text
harness S09 definitivo con S09-RF-01/02 chiusi
status M2-S09 IN PROGRESS
nessun candidate JSON
nessun acceptance.md
active aid presente
nessuna modifica non committata
```

Esegui il final gate da un worktree detached e pulito dell’esatto nuovo
candidate SHA.

## 9.1 Quality e ambiente

Esegui almeno:

```text
uv lock --check
uv sync --locked
due build pulite e indipendenti
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Registra:

```text
CPython 3.14.x
uv
Hatchling
pytest
Ruff
Pyright
Linux distribution / kernel / architecture
PostgreSQL version / database identity / SELECT 1
```

## 9.2 Bundle, scenario e predicati

Esegui direttamente e senza retry:

```text
32-bundle deduplicated union
83-scenario deduplicated union
predicate assertion gate
```

Usa il runner corretto e richiedi:

```text
command exit status            0
M2-VER                         32 / 32 PASS
M2-AC                          32 / 32 PASS
M2-OUT                         16 / 16 covered
canonical scenarios            83 / 83 PASS
safety predicates              21 / 21 PASS
skip / xfail / rerun           0 / 0 / 0
missing/BLOCKED targets        0
```

Non usare il solo full-suite exit code per derivare i ledger.

## 9.3 Layer e regressione

Esegui almeno:

```text
complete delivered regression
complete M2 functional suite
all traceability
S06 / T8 completo
S07 / T9 completo
S08 / T10 completo
schema / Alembic
API / error / CLI
runtime / schema-guard / Health
PostgreSQL / concurrency
non-PostgreSQL
repository completa
```

Richiedi:

```text
15 authoritative tables
one base / one head / current 0001_m2_kernel
compare_metadata == []
63 business HTTP / 1 Health
63 CLI remote / 8 local / 65 examples
23 public error codes
131 negative surfaces
10 contract-quality gates
installed T9 PASS
supported-path 40P01 = 0
unexpected 40001 = 0
negative controls = 40P01 x1 / 40001 x2
open findings = 0
new unexplained warnings = 0
```

La deprecazione Starlette/FastAPI già censita può restare l’unica warning.

## 9.4 Artifact reproducibility

Costruisci due volte dal nuovo candidate SHA e verifica nuovamente:

```text
wheel                  netauto-0.2.0-py3-none-any.whl
wheel size             165978 byte
wheel members          77
wheel SHA-256          38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size      48238 byte
runtime packages       29
runtime lock SHA-256   0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

Una modifica test-only non deve cambiare l’artifact. Se cambia, fermati e
identifica il drift.

Rimuovi worktree, `dist/`, wheel, sdist, JUnit, log e output temporanei dopo aver
conservato soltanto i dati bounded destinati all’evidence.

---

## 10. Pubblicazione del nuovo candidate record

Soltanto dopo il full gate completamente verde crea esattamente:

```text
docs/milestones/M2/evidence/candidate-<NEW_CANDIDATE_SHA>.json
docs/milestones/M2/acceptance.md
```

Il nuovo record deve:

```text
usare FinalEvidenceRecord
usare stable_evidence_json()
validare in phase="implementer"
contenere candidate_commit = NEW_CANDIDATE_SHA
contenere reviewer_decision = null
contenere open_findings = ()
contenere soltanto risultati realmente rieseguiti sul nuovo SHA
contenere 32 / 83 / 21 ledger esatti, tutti PASS
contenere gli exit status effettivi dei runner corretti
non contenere secret, DB URL, DSN o userinfo
```

Non copiare il vecchio JSON e non modificarne semplicemente la SHA.

`acceptance.md` deve tornare al candidate state:

```text
# M2 Final Acceptance Candidate
Status: CANDIDATE READY FOR REVIEW
reviewer decision PENDING / reviewer-owned
M2-S09 is not COMPLETED
M2 is not DELIVERED
```

Aggiorna `status.md` soltanto a:

```text
M2-S09    CANDIDATE READY FOR REVIEW
M2        NOT DELIVERED
```

Non impostare:

```text
M2-S09 COMPLETED
M2 DELIVERED
reviewer_decision ACCEPTED
AS-IS consolidation started
```

Commit consigliato:

```text
docs(m2): publish replacement final acceptance candidate
```

Pusha soltanto su `M2` e verifica branch sincronizzato e worktree pulito.

---

## 11. Exact-remote publication-integrity gate

Sull’esatto remote evidence HEAD riesegui almeno:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright
collection
real S09 record/acceptance tests
implementer-phase evidence validation
all traceability
32-bundle target union
83-scenario/predicate target union
S06 / T8
S07 / T9
S08 / T10
schema / Alembic
API / error / CLI
runtime / schema-guard / Health
PostgreSQL / concurrency
non-PostgreSQL
full repository
artifact hash comparison
```

Il compact candidate JSON può essere escluso esclusivamente dal formatter
post-publication quando ciò è necessario a preservare byte-per-byte
`stable_evidence_json()`. Ruff lint deve verificare l’intero tree. Il candidate
SHA privo del JSON deve aver superato `ruff format --check .` senza esclusioni.

Se pubblichi un successivo commit soltanto per registrare in `status.md` i
risultati di integrità, riesegui sul nuovo final remote HEAD almeno:

```text
record/acceptance lifecycle
Ruff lint e formatter policy
Pyright
collection
traceability
full repository
artifact hash
```

Non creare una catena infinita di commit che tentano di descrivere se stessi.
I risultati dell’ultimo exact-remote gate possono essere riportati nel handoff
senza un ulteriore commit.

Se qualunque gate post-publication fallisce:

```text
riporta M2-S09 a IN PROGRESS
mantieni M2 NOT DELIVERED
ritira dal working tree il candidate JSON e acceptance.md invalidati
preserva il failure nella cronologia/status
non consegnare il candidate
```

Un successivo passaggio isolato non sostituisce il primo failure.

---

## 12. Failure policy

Se un focused gate fallisce:

```text
mantieni M2-S09 REVIEW CHANGES REQUIRED o IN PROGRESS, secondo la fase
correggi soltanto S09-RF-01 / S09-RF-02
non congelare un candidate
```

Se un full candidate gate fallisce:

```text
M2-S09 IN PROGRESS
M2 NOT DELIVERED
nessun candidate JSON
nessun acceptance.md candidate-ready
```

Non usare:

```text
retry automatico
rerun plugin
skip
xfail
warning suppression broad
target union ridotta
PostgreSQL sostitutivo
rilassamento del validator
riuso del vecchio evidence ledger
```

---

## 13. Commit discipline

Non usare:

```text
git add .
git add -A
git add --all
```

Stage soltanto path esplicitamente verificati.

Sequenza raccomandata:

```text
1. test(m2): close S09 harness review findings
       harness/tests/docs lifecycle
       stato RCR e record rifiutato ancora presenti

2. docs(m2): start replacement S09 candidate cycle
       status IN PROGRESS
       vecchio JSON rimosso
       vecchio acceptance.md rimosso

3. eventuale ulteriore harness commit test-only
       prima di congelare il nuovo candidate SHA

4. docs(m2): publish replacement final acceptance candidate
       nuovo JSON
       nuovo acceptance.md
       status candidate-ready
```

Non creare PR, Actions, tag, Release, artifact publication o merge.

---

## 14. Final report

Riporta soltanto fatti verificati:

```text
branch
starting remote HEAD
reviewer rejection ancestry
review-fix commit
replacement-cycle commit
NEW_CANDIDATE_SHA
evidence/status commit
final remote HEAD
HEAD/origin/remote equality
ahead/behind
clean worktree

file modificati
S09-RF-01 closure
S09-RF-02 closure
exact lifecycle matrix tests
fail-closed runner tests
old rejected record retirement
new candidate record path
reviewer_decision null

quality/build/reproducibility
bundle union
32 evidence bundles
32 acceptance criteria
16 outcomes
83 scenarios
21 predicates
blocking/progress assertions
S06/T8
S07/T9
S08/T10
schema/Alembic/API/CLI/Health
PostgreSQL
non-PostgreSQL
full suite
collection
skip/xfail/rerun
warning census
SQLSTATE census
compare_metadata
open findings
post-publication integrity gate

wheel e runtime-lock identity
PostgreSQL version/database/probe senza credenziali
production/API/CLI/Health/schema/migration/dependency boundaries invariati
assenza di PR/Action/tag/Release/artifact publication
```

L’unico handoff implementer ammesso è:

```text
M2-S09    CANDIDATE READY FOR REVIEW
M2        NOT DELIVERED
```

La successiva decisione reviewer dovrà poter usare senza modifiche di harness:

```text
REVIEW CHANGES REQUIRED
oppure
ACCEPTED + M2-S09 COMPLETED
```

M2 delivery, AS-IS consolidation e merge restano attività separate e
reviewer/human-owned.
