# Codex implementation prompt — M2-S09

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

Questo file autorizza esclusivamente:

```text
M2-S09 — Full M2 acceptance and delivery-candidate gate
```

È subordinato a `AGENTS.md`, al current AS-IS consegnato, al contract e all’architecture set M2 `FINAL / FROZEN`, a `steps.md`, alla technology baseline ratificata e allo stato reviewer-owned in `status.md`.

Il prompt non crea semantica, non riapre l’architettura e non autorizza nuove capability. In caso di conflitto prevalgono sempre le authority normative.

---

## 1. Assignment e baseline

Lavora direttamente sul branch:

```text
M2
```

Baseline implementativa accettata e obbligatoria nell’ancestry:

```text
95a61e0815472e85be55828fa546e916c0cb3e66
docs(m2): publish relative-import corrected S08 candidate
```

Il reviewer-owned commit che contiene questo aid deve avere già registrato:

```text
M2-S08    COMPLETED
M2-S09    READY
```

La SHA del commit di acceptance/prompt publication è dinamica: dopo `git pull --ff-only`, usa l’esatto `origin/M2` corrente. Non tornare a `95a61e...`, non rebaseare e non riscrivere la cronologia.

Preserva nell’ancestry almeno:

```text
1f8e82de73d953830a6b31045ec96dfe19116dd9
8ee9e540d24ecf07c8688350a03162a89d0991ce
954fd86f576f3b4a0ec4efb8849cf059c801dfef
664d8b02323f17daeada898d448c4a8a9c0e6a51
95a61e0815472e85be55828fa546e916c0cb3e66
```

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

Prima di modificare qualsiasi file verifica:

```text
git branch --show-current                  M2
git pull --ff-only                         successo / già aggiornato
HEAD == origin/M2                          sì
working tree                               pulito
origin/M2 contiene 95a61e...               sì
questo prompt esiste all’HEAD               sì
M2-S08                                      COMPLETED
M2-S09                                      READY
contract                                    FINAL / FROZEN
architecture set                            FINAL / FROZEN
steps                                       FINAL / FROZEN
reopen architetturali aperti                nessuno
M2                                          NOT DELIVERED
```

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
docs/milestones/M2/wip/M2-S09-codex-prompt.md
```

Ispeziona inoltre almeno:

```text
tests/support/m2_evidence.py
tests/test_m2_s08_evidence.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_traceability.py
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py

tests/support/s07_release.py
tests/test_m2_s07_distribution.py
tests/test_m2_s07_linux.py
tests/test_m2_s07_trust.py

tests/conftest.py
pyproject.toml
uv.lock
src/netauto/release/runtime.pylock.toml
```

Se README, branch, status, steps o frozen authority non concordano, fermati prima di modificare il repository.

### 2.1 PostgreSQL pre-flight

`TEST_DATABASE_URL` deve essere presente e fornito dall’ambiente.

Un hostname locale o loopback non è di per sé un blocker. Il target è valido soltanto quando:

```text
forma URL                      postgresql+psycopg
backend                        PostgreSQL reale
provisioning                   esterno al test process NETAUTO
database                       dedicato e conforme ai safety check esistenti
fallback                       nessuno
SQLite/fake/embedded           assenti
Docker/Testcontainers          non usati
```

Esegui un probe bounded e registra senza credenziali:

```text
PostgreSQL server version
current database identity
SELECT 1
```

Non stampare né committare URL, user, password, DSN o secret.

### 2.2 Ambiente supportato

Registra l’ambiente effettivo:

```text
CPython 3.14.x
uv
Hatchling
pytest
Ruff
Pyright
Linux distribution / kernel / architecture
PostgreSQL
```

Se l’ambiente non appartiene alla baseline ratificata, la final acceptance non può essere dichiarata candidate-ready.

---

## 3. Obiettivo e confine della slice

M2-S09 deve eseguire il final gate contro:

```text
un solo candidate commit identificato
la wheel costruita da quel candidate commit
un solo record evidence durevole e validato
```

La slice introduce **zero capability di produzione**.

Sono autorizzati soltanto:

```text
acceptance/evidence harness test-only
lifecycle test per aid/evidence/acceptance
command/result collection test-only
documentazione evidence e acceptance
status operativo M2
correzioni di difetti del final-gate harness o della documentazione S09
```

Un finding di produzione deve essere trattato così:

```text
implementation defect in una slice precedente
    -> STOP final acceptance
    -> identifica owning slice
    -> registra il finding
    -> riapertura reviewer-owned della slice proprietaria

architecture defect / decisione mancante
    -> STOP del punto interessato
    -> formal reopen / propagation / re-freeze
```

Non correggere silenziosamente un difetto di produzione dentro S09.

### 3.1 File ammessi

Sono ammessi, quando necessari:

```text
tests/support/s09_acceptance.py
tests/test_m2_s09_acceptance.py
un altro helper test-only S09 strettamente necessario

tests/test_m2_s08_evidence.py
    solo per la transizione lifecycle S08 -> S09

tests/test_m2_s08_negative_surface.py
    solo per la transizione lifecycle dell’execution aid

tests/test_m2_traceability.py
    solo per registri final-gate derivati dalle authority esistenti

docs/milestones/M2/evidence/README.md
docs/milestones/M2/evidence/candidate-<candidate-sha>.json
docs/milestones/M2/acceptance.md
docs/milestones/M2/status.md
```

È ammesso un piccolo script test-only standard-library per eseguire target, leggere JUnit XML e costruire il ledger, purché non introduca una seconda authority.

### 3.2 File e superfici vietate

Non modificare:

```text
src/netauto/ production code
public API / DTO / error catalog
CLI grammar, registry, rendering o terminal behavior
Health contract
SQLAlchemy metadata
schema / DDL / indici
migration 0001_m2_kernel o Alembic graph
pyproject dependencies
uv.lock
runtime.pylock.toml
versione 0.2.0
wheel content
frozen contract / architecture / steps
```

Non creare:

```text
nuove route o command
nuove tabelle o migration
nuovi setting
auth o server-side TLS
Docker / Kubernetes / systemd product
GitHub Actions
PR
tag
GitHub Release
artifact publication
merge
AS-IS consolidation
```

---

## 4. Transizioni lifecycle obbligatorie di S09

La pubblicazione del nuovo aid e la creazione futura dell’evidence record cambiano intenzionalmente due stati che S08 verificava come ancora assenti.

Questa non è una riduzione della verifica: è la transizione frozen da “schema preparato” a “record finale popolato”.

### 4.1 WIP aid lifecycle

Il test:

```text
test_wip_provenance_is_complete_and_never_implementation_authority
```

va reso phase-aware per l’aid attivo:

```text
durante M2-S09 READY / IN PROGRESS / CANDIDATE READY FOR REVIEW
    M2-S09-codex-prompt.md presente
    M2-S08-review-fixes-codex-prompt.md assente

dopo reviewer-owned M2-S09 COMPLETED
    M2-S09-codex-prompt.md assente
```

Preserva esattamente:

```text
19 historical WIP disposition rows
2 permanent closure records
0 implementation dependency on WIP
0 unclassified historical document
at most one active execution aid
```

Il test deve simulare anche la rimozione reviewer-owned futura del prompt e restare verde.

Non rendere normativa la presenza del prompt e non aggiungerlo alle 19 disposition storiche.

### 4.2 Evidence/acceptance lifecycle

Il test S08 che oggi richiede:

```text
evidence/ contiene solo README.md
acceptance.md assente
```

va trasformato in una verifica lifecycle finita:

```text
S09 READY / IN PROGRESS prima della pubblicazione evidence
    evidence/README.md presente
    nessun candidate JSON
    acceptance.md assente

S09 CANDIDATE READY FOR REVIEW
    evidence/README.md presente
    esattamente un candidate-<40hex>.json
    acceptance.md presente
    reviewer_decision null

S09 COMPLETED dopo reviewer action
    stesso candidate record
    reviewer_decision finita e reviewer-owned
    execution aid ritirato
```

Non ammettere più record candidati contemporanei e non permettere file extra non classificati nella directory evidence.

### 4.3 Stato operativo iniziale

Nel primo commit S09 imposta:

```text
M2-S09    IN PROGRESS
M2        NOT DELIVERED
```

senza creare ancora il candidate-specific evidence record.

---

## 5. Modello obbligatorio di candidate identity

Il record JSON non può riferirsi al commit che lo crea senza riscrivere la storia. S09 usa quindi due identità distinte e non ambigue.

### 5.1 Candidate commit

Il **candidate commit** è l’esatto commit che contiene:

```text
production accettata fino a S08
S09 acceptance harness definitivo
lifecycle test definitivo
nessun candidate-specific JSON
nessun acceptance.md
status M2-S09 IN PROGRESS
```

Dopo ogni eventuale correzione del solo harness S09:

```text
committa
pusha su M2
verifica HEAD == origin/M2 == remote M2
verifica worktree pulito
```

Solo allora congela:

```text
CANDIDATE_SHA = git rev-parse HEAD
```

`CANDIDATE_SHA` deve essere presente sul remoto prima di eseguire il final gate.

### 5.2 Evidence publication commit

Dopo che **tutti** i gate sul candidate SHA sono passati, un commit successivo crea:

```text
docs/milestones/M2/evidence/candidate-<CANDIDATE_SHA>.json
docs/milestones/M2/acceptance.md
status M2-S09 CANDIDATE READY FOR REVIEW
```

Il campo JSON:

```text
candidate_commit
```

contiene `CANDIDATE_SHA`, non la SHA del commit evidence.

La commit evidence non è una nuova build candidate. Deve contenere soltanto evidence, acceptance/status e gli eventuali test che validano quei file.

### 5.3 Exact candidate worktree

Esegui il final gate da un checkout pulito e immutabile del candidate SHA, per esempio mediante un worktree detached:

```text
git worktree add --detach <temp-dir> <CANDIDATE_SHA>
```

Nel worktree candidate:

```text
nessuna modifica
nessun PYTHONPATH verso il checkout principale
uv sync --locked
build e test dall’esatto SHA
```

Rimuovi il worktree temporaneo soltanto dopo aver conservato i dati bounded necessari al record.

Non usare il working tree dell’evidence commit come sostituto del candidate gate.

---

## 6. Harness finale e registri derivati

Non creare una seconda authority parallela.

Deriva il final gate esclusivamente dai registri permanenti già presenti, inclusi:

```text
M2_OUTCOMES
M2_ACCEPTANCE_CRITERIA
M2_EVIDENCE_BUNDLES
M2_EVIDENCE_TO_TARGETS
M2_CONCURRENCY_SCENARIOS
M2_PREDICATE_TO_SCENARIOS
PUBLIC_HTTP_OPERATIONS
CLI_REMOTE_OPERATION_COVERAGE
M2_AS_IS_GUARANTEE_TO_TARGETS
M2_NEGATIVE_SURFACE_TO_TARGETS
M2_CONTRACT_QUALITY_GATES
```

È ammesso introdurre un registry S09 derivato, per esempio:

```text
S09_FINAL_GATE_TARGETS
S09_BUNDLE_TARGET_UNION
S09_SCENARIO_TARGET_UNION
```

ma deve essere costruito programmaticamente dai registri sopra e machine-checkato contro di essi.

Non copiare manualmente 32 bundle, 83 scenario o 21 predicati in una seconda mappa divergente.

### 6.1 Target resolution

Il harness deve verificare prima dell’esecuzione:

```text
32 / 32 bundle presenti
ogni bundle IMPLEMENTED e non vuoto
ogni concrete target esiste ed è raccolto
83 / 83 scenario presenti
ogni scenario ha recipe e target concreti
21 / 21 predicati presenti
ogni predicato ha scenario coverage
nessun target orfano o nome non risolvibile
```

### 6.2 Result collection

Usa un meccanismo deterministico e dependency-free, per esempio:

```text
pytest --junitxml <temp-file>
standard-library XML parser
```

oppure un equivalente pytest plugin test-only.

Il collector deve registrare per ogni comando:

```text
argv esatto come array di stringhe
exit status
durata
selected
passed
skipped
xfailed
rerun
warnings
```

Per target parametrizzati, il target base è `PASS` solo quando tutte le istanze raccolte sono passate e nessuna è skipped/xfailed/rerun.

Non usare il solo exit code della full suite per derivare i ledger per bundle o scenario.

### 6.3 Ledger derivation

Un bundle è `PASS` solo se tutti i suoi target concreti sono passati sul candidate.

Uno scenario è `PASS` solo se tutti i target della sua recipe sono passati e le blocking/progress assertion richieste sono state eseguite.

Un predicato è `PASS` solo se tutti gli scenario che ne costituiscono la copertura obbligatoria sono `PASS` e la relativa predicate assertion machine-check è passata.

`M2-AC-xx` passa soltanto quando il corrispondente `M2-VER-xx` passa.

`M2-OUT-*` è coperto soltanto attraverso la traceability frozen e bundle `PASS`; la documentazione da sola non conta.

---

## 7. Candidate evidence record

Crea esattamente:

```text
docs/milestones/M2/evidence/candidate-<CANDIDATE_SHA>.json
```

Usa direttamente:

```text
tests/support/m2_evidence.py
FinalEvidenceRecord
validate_evidence_record(..., phase="implementer")
stable_evidence_json(...)
```

Non serializzare manualmente un formato concorrente.

### 7.1 Identità e artifact

Registra valori misurati:

```text
schema_version           1
candidate_commit         CANDIDATE_SHA
branch                   M2
release_version          0.2.0
wheel path/name
wheel byte size
wheel member count
wheel SHA-256
runtime-lock source path
runtime-lock byte size
runtime-lock package count
runtime-lock SHA-256
```

Il lock path resta esattamente:

```text
src/netauto/release/runtime.pylock.toml
```

### 7.2 Environment

Registra:

```text
CPython
uv
Hatchling
PostgreSQL
Linux
```

Imposta `locked_environment_confirmed` e `build_confirmed` a `true` soltanto dopo i relativi gate riusciti.

### 7.3 Command ledger

Il ledger contiene tutti i comandi materialmente necessari al final gate, almeno:

```text
uv lock --check
uv sync --locked
uv build
second clean reproducibility build
Ruff format check
Ruff lint
Pyright
collection
32-bundle target union
83-scenario target union
predicate/traceability gate
T8 / complete S06
T9 installed artifact
T10 / complete S08
schema/Alembic
API/error/CLI
runtime/schema-guard/Health
PostgreSQL/concurrency
non-PostgreSQL
full repository
post-publication evidence validation
```

Non inserire `TEST_DATABASE_URL` o secret in argv. Passali soltanto tramite environment.

### 7.4 Exact ledgers

Il record deve contenere esattamente:

```text
evidence_bundles    M2-VER-01 ... M2-VER-32
scenarios           83 canonical IDs
predicates          21 canonical safety predicates
```

Per un candidate consegnabile, ogni valore è:

```text
PASS
```

Non utilizzare `IMPLEMENTED` come sostituto di esecuzione.

### 7.5 Schema e operations

Registra e verifica:

```text
table_count             15
Alembic bases           (0001_m2_kernel,)
Alembic heads           (0001_m2_kernel,)
database revisions      (0001_m2_kernel,)
compare_metadata        ()

business HTTP           63
Health HTTP             1
CLI remote              63
CLI local               8
CLI examples            65
```

### 7.6 Installed T9 e runtime census

Per un candidate consegnabile:

```text
installed_t9            PASS
skipped                 0
xfailed                 0
rerun                   0
supported_40p01         0
unexpected_40001        0
open_findings           ()
```

La warning terza parte Starlette/FastAPI già censita può essere registrata con il conteggio effettivo. Qualunque nuova warning non spiegata blocca il candidate.

### 7.7 Reviewer ownership

Il record implementer deve contenere:

```text
reviewer_decision       null
```

Valida obbligatoriamente:

```text
validate_evidence_record(record, expectations, phase="implementer")
```

Non scrivere:

```text
ACCEPTED
REVIEW CHANGES REQUIRED
COMPLETED
DELIVERED
```

nel campo reviewer-owned.

### 7.8 Safety

Il record non deve contenere:

```text
database URL
DSN
userinfo URL
username/password
credential
token
private key
secret value
raw log contenente secret
```

HTTP/HTTPS endpoint senza userinfo è ammesso dal formato, ma includilo soltanto quando realmente necessario alla command evidence.

---

## 8. `acceptance.md`

Crea:

```text
docs/milestones/M2/acceptance.md
```

Il documento è evidence durevole, non semantic authority.

Header richiesto:

```text
# M2 Final Acceptance Candidate

Status: CANDIDATE READY FOR REVIEW
```

Deve riportare almeno:

```text
candidate SHA
evidence JSON path
release e artifact hash
runtime-lock hash
environment versions
locked/build/reproducibility result
32 / 32 bundle PASS
32 / 32 acceptance criteria PASS
16 / 16 outcomes covered
83 / 83 scenarios PASS
21 / 21 predicates PASS
blocking/progress result
schema/head/drift result
63 API / 63 CLI result
T9 result
quality/full-suite result
warning e SQLSTATE census
open findings = 0
reviewer decision = PENDING / reviewer-owned
```

Può riassumere i 32/83/21 ledger e puntare al JSON per il dettaglio esatto; non deve duplicare manualmente una seconda matrice divergente.

Registra chiaramente:

```text
M2-S09 non COMPLETED
M2 non DELIVERED
AS-IS consolidation non iniziata
merge non eseguito
```

Non precompilare un’approvazione reviewer.

---

## 9. Artifact e build reproducibility

Esegui due build pulite e indipendenti dal candidate SHA.

Per entrambe verifica:

```text
un solo wheel atteso
netauto-0.2.0-py3-none-any.whl
member inventory
METADATA version 0.2.0
embedded runtime lock
server + CLI + DTO + Alembic resources
nessun source checkout dependency
```

Confronta fra le due build:

```text
wheel SHA-256
wheel byte size
member count
embedded runtime-lock bytes/hash
```

Il risultato atteso dalla boundary S08 è:

```text
wheel size / members    165978 bytes / 77
wheel SHA-256           38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60
runtime lock size       48238 bytes
runtime lock SHA-256    0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

Misura nuovamente. Se il risultato differisce, non aggiornare semplicemente l’atteso: identifica il drift e blocca il candidate.

Non committare:

```text
dist/
wheel
sdist
venv
JUnit XML
raw log
coverage artifact
secret file
```

---

## 10. Verification gate completo

T7 resta supplementare e non è obbligatorio per l’accettazione. Devi eseguire tutti gli altri layer richiesti:

```text
T0
T1
T2
T3
T4
T5
T6
T8
T9
T10
```

### 10.1 Quality e collection

Esegui sul candidate SHA:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

Richiedi:

```text
exit 0
Pyright 0 errors / 0 warnings
nessun Ruff finding
nessun file formatter-dirty
collection finita e stabile
```

### 10.2 Tutti i 32 evidence bundle

Costruisci la union deduplicata dei target di:

```text
M2-VER-01 ... M2-VER-32
```

Eseguila direttamente sul candidate SHA e costruisci il ledger bundle-per-bundle dai risultati concreti.

Richiedi:

```text
32 / 32 PASS
nessun target mancante
nessun target skipped/xfailed/rerun
```

### 10.3 Tutti gli 83 scenario

Esegui la union deduplicata dei concrete target dei **tutti** gli 83 scenario canonici, non soltanto i 51 consegnati da M1.

Verifica:

```text
83 / 83 ID presenti
83 / 83 PASS
51 / 51 delivered scenario preservati
32 / 32 M2 scenario PASS
21 / 21 predicate PASS
required blocking assertion PASS
required progress assertion PASS
```

Non sostituire questa esecuzione con la full suite generica.

### 10.4 SQLSTATE policy

Per i path supportati:

```text
40P01                 0
unexpected 40001      0
```

I negative control devono restare nel censimento finito atteso:

```text
40P01 x1
40001 x2
```

Un SQLSTATE supportato vietato blocca il candidate anche quando un retry successivo passa.

Non usare retry automatici.

### 10.5 AS-IS e regressione funzionale

Esegui almeno:

```text
complete delivered regression
complete M2 functional suite
all S05
all S06 / T8
all S07 / T9
all S08 / T10
M1 traceability
M2-S00 traceability
M2 traceability
```

### 10.6 API, CLI e negative surface

Esegui e verifica:

```text
63 business HTTP operations
1 Health operation
63 remote CLI mappings
8 local commands
65 examples
23 public error codes
strict request/response/error behavior
no auth / 401 / 403 / securitySchemes
no insecure or skip-verify option
no direct CLI kernel/database import
no hidden mutation GET
no automatic migration
131 / 131 negative surfaces asserted
10 / 10 contract-quality gates
```

### 10.7 Schema, Alembic e startup

Esegui:

```text
fresh installed downgrade/base/upgrade/head where owned by T9
one base / one head
current revision 0001_m2_kernel
15-table positive inventory
negative table/constraint/index inventory
compare_metadata == []
startup exact-head guard
startup mismatch refusal
no automatic migrate/stamp/repair
```

### 10.8 Installed wheel / T9

Da wheel installata fuori dal checkout, esegui l’intero T9:

```text
exact lock sync
wheel install --no-deps
installed package/entrypoints
installed Alembic graph
explicit migration
startup before/after migration
Health 200
business read
CLI non-interattiva
CLI PTY
orderly stop/disposal
fresh restart
revision mismatch
real-PG transport cut -> Health 503
HTTPS trusted / untrusted / hostname mismatch
secret non-leakage
Linux operator procedure
```

Non riutilizzare un vecchio artifact senza ricostruirlo dal candidate SHA.

### 10.9 PostgreSQL e non-PostgreSQL

Esegui separatamente:

```text
PostgreSQL/concurrency suite completa
non-PostgreSQL suite completa
```

Poi esegui:

```text
repository suite completa
```

Richiedi:

```text
skip / xfail / rerun    0 / 0 / 0
nuove warning           0
full suite              PASS
```

---

## 11. S09 acceptance tests permanenti

Aggiungi prove permanenti per il record reale, almeno:

```text
candidate JSON filename matches candidate_commit
exactly one candidate JSON exists
record parses into FinalEvidenceRecord
stable_evidence_json(record) equals committed bytes
implementer-phase validation PASS
reviewer_decision is null in candidate state
exact 32 / 83 / 21 identifier sets
all candidate ledger values PASS
schema and operation census exact
artifact/environment values non-empty and safe
no secret / DB URL / userinfo
acceptance.md matches JSON identity and summary
candidate SHA is an ancestor of evidence HEAD
candidate SHA differs from evidence publication SHA
WIP lifecycle accepts active S09 aid and future removal
evidence lifecycle accepts pre-record, candidate and future reviewer states
no acceptance.md before candidate publication in candidate SHA
```

Le prove post-publication devono validare il record realmente committato, non soltanto una fixture sintetica.

Non rendere il test dipendente da timestamp assoluti o path `/tmp` specifici.

---

## 12. Failure handling

Se qualunque gate sul candidate SHA fallisce:

```text
M2-S09    IN PROGRESS
M2        NOT DELIVERED
```

Non creare il candidate-specific JSON e non creare `acceptance.md` come se il gate fosse passato.

Puoi registrare in `status.md`:

```text
candidate SHA tentata
comando fallito
target/finding
ambiente
scope proprietario
```

Non usare:

```text
retry automatico
rerun plugin
skip
xfail
warning suppression broad
riduzione del target union
sostituzione PostgreSQL
rilassamento del validator
```

Se il failure riguarda soltanto il nuovo S09 harness/documentation e le authority determinano univocamente la correzione, correggilo dentro S09 e ripeti un nuovo ciclo completo con una nuova candidate SHA.

Una run fallita non può essere riabilitata da un successivo passaggio isolato: serve un nuovo exact-candidate gate completo.

---

## 13. Commit protocol

### 13.1 Harness commit

Prima del final gate, committa soltanto il lifecycle/harness S09 necessario, per esempio:

```text
test(m2): add S09 final acceptance harness
```

Aggiorna `status.md` a `M2-S09 IN PROGRESS` nello stesso candidato o in un commit documentale immediatamente precedente.

Pusha e congela il nuovo `CANDIDATE_SHA` soltanto con:

```text
HEAD == origin/M2 == remote M2
ahead / behind == 0 / 0
working tree pulito
```

### 13.2 Evidence publication commit

Dopo il final gate completamente verde crea un commit equivalente a:

```text
docs(m2): publish final acceptance candidate evidence
```

Contenuto consentito:

```text
docs/milestones/M2/evidence/candidate-<CANDIDATE_SHA>.json
docs/milestones/M2/acceptance.md
docs/milestones/M2/status.md
S09 tests che validano i file reali, se non già presenti nel candidate
```

Preferisci che i test di validazione real-file siano già nel candidate commit. Se richiedono il file non ancora esistente, devono essere lifecycle-aware e passare sia prima sia dopo la pubblicazione.

Non usare:

```text
git add .
git add -A
git add --all
```

Stage soltanto path esplicitamente verificati.

### 13.3 Stato implementer finale

Imposta soltanto:

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

---

## 14. Exact-remote post-publication gate

Dopo il push dell’evidence commit verifica:

```text
HEAD == origin/M2 == remote M2
ahead / behind == 0 / 0
working tree pulito
```

Sull’esatto evidence HEAD remoto esegui almeno:

```text
uv lock --check
uv sync --locked
uv build
Ruff format/check
Pyright
collection
S09 record/acceptance tests
implementer-phase evidence validation
all traceability tests
32-bundle target union
83-scenario target union
S06 / T8
S07 / T9
S08 / T10
schema/Alembic
API/error/CLI
runtime/schema-guard/Health
PostgreSQL/concurrency
non-PostgreSQL
full repository
```

Ricostruisci la wheel dall’evidence HEAD e richiedi lo stesso hash del candidate artifact. Poiché la pubblicazione è docs/test-only, una differenza indica drift e blocca il handoff.

Se qualunque post-publication gate fallisce:

```text
riporta M2-S09 a IN PROGRESS
mantieni M2 NOT DELIVERED
non consegnare il candidate
```

Il record fallito non deve restare presentato come candidate-ready.

---

## 15. Reviewer handoff

Il report finale implementer deve riportare soltanto fatti verificati:

```text
branch
starting reviewer-owned HEAD
harness commit
CANDIDATE_SHA
evidence/status commit
final remote HEAD
HEAD/origin/remote equality
ahead/behind
clean worktree

candidate evidence filename
acceptance.md path
reviewer_decision null
wheel filename/size/member/hash
runtime-lock size/package/hash
environment versions
PostgreSQL identity/probe senza credenziali

quality/build/reproducibility
32 bundle
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

file modificati
production/schema/API/CLI/dependency boundaries invariati
assenza di PR/Action/tag/Release/artifact publication
```

L’unico handoff ammesso è:

```text
M2-S09    CANDIDATE READY FOR REVIEW
M2        NOT DELIVERED
```

Il reviewer dovrà successivamente:

```text
validare il record in reviewer phase
impostare ACCEPTED o REVIEW CHANGES REQUIRED
marcare eventualmente M2-S09 COMPLETED
ritirare questo execution aid
```

La consegna M2, l’AS-IS consolidation e il merge restano fasi separate e reviewer/human-owned.
