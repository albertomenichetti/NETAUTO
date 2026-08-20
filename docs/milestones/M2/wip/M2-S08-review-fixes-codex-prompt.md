# Codex review-fix prompt — M2-S08

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

Questo file autorizza esclusivamente la continuazione correttiva di:

```text
M2-S08 — Integrated regression, traceability and negative-surface closure
```

È subordinato a `AGENTS.md`, all’AS-IS consegnato, al contract e all’architecture set M2 `FINAL / FROZEN`, a `steps.md`, alla technology baseline ratificata e allo stato reviewer-owned in `status.md`.

---

## 1. Assignment e baseline

Lavora direttamente sul branch:

```text
M2
```

Candidate rifiutato e baseline di ancestry obbligatoria:

```text
e39f1aca2f2f4ad4f14d3487b8b0c0c8918964b5
docs(m2): publish corrected S08 candidate evidence
```

Reviewer-owned reopen obbligatorio nell’ancestry:

```text
8e615d4223ee3a8a35cccebaa278cf23d740045a
docs(m2): reopen S08 for final verification closure
```

Queste SHA sono baseline di ancestry, non l’HEAD atteso: la pubblicazione di questo prompt crea necessariamente commit successivi.

Correggi esclusivamente:

```text
S08-VRF-05
    import-time Alembic mutation closure

S08-VRF-06
    semantic closure delle superfici negative astratte

S08-VRF-07
    reviewer ACCEPTED coherence nel futuro evidence record
```

Mantieni chiusi e invariati:

```text
S08-VRF-01
    lifecycle-safe WIP census

S08-VRF-02
    entry-specific negative-surface mapping

S08-VRF-03
    alias-safe and call-graph-aware Alembic analysis

S08-VRF-04
    implementer/reviewer evidence phases

PTY reverse-search correction
    già pubblicata e verificata
```

Non ripartire da zero. Non eseguire reset, rebase, force-push o riscrittura della cronologia.

Preserva nell’ancestry almeno:

```text
3d794d25317425254440f4e4b711ebfb63113edf
b8c78c712d61514998281ea170e7606e1eb99781
9027b02b7f2b949cd7674adfa7c3fe3758eacda3
02a3a98ce5fc14419bcc795a8520ad1659140805
42843b4c885ee550a3e7b3dfc21896d9ae8a1ba1
e39f1aca2f2f4ad4f14d3487b8b0c0c8918964b5
8e615d4223ee3a8a35cccebaa278cf23d740045a
```

---

## 2. Mandatory pre-flight

Prima di modificare file, verifica:

```text
git branch --show-current              M2
HEAD == origin/M2                      sì
working tree                            pulito
origin/M2 contiene e39f1aca...         sì
origin/M2 contiene 8e615d42...         sì
questo prompt esiste all’HEAD           sì
M2-S08                                  REVIEW CHANGES REQUIRED o IN PROGRESS
M2-S09                                  BLOCKED
contract                                FINAL / FROZEN
architecture set                        FINAL / FROZEN
steps                                   FINAL / FROZEN
reopen architetturali aperti            nessuno
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
docs/milestones/M2/architecture/provenance.md
docs/milestones/M2/architecture/verification.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/milestones/M2/architecture/cli.md
docs/milestones/M2/architecture/health.md
docs/milestones/M2/architecture/persistence.md
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

docs/milestones/M2/wip/M2-S08-review-fixes-codex-prompt.md
```

Ispeziona inoltre:

```text
tests/support/s08_static.py
tests/support/m2_evidence.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_s08_evidence.py
tests/test_m2_traceability.py
docs/milestones/M2/evidence/README.md
```

### `TEST_DATABASE_URL`

`TEST_DATABASE_URL` è **externally supplied** quando è fornito esplicitamente dall’ambiente e il test code NETAUTO non lo provisiona, non lo inventa e non lo sostituisce silenziosamente.

Un hostname loopback o locale non è, da solo, un blocker.

Devi verificare concretamente che:

```text
URL                              presente
forma supportata                 postgresql+psycopg
server raggiungibile             sì
backend reale                    PostgreSQL
versione PostgreSQL              rilevata dalla connessione reale
target test dedicato/sicuro      conforme ai controlli esistenti del test support
provisioning da test code        assente
fallback SQLite/fake/local auto  assente
```

Non inventare credenziali o hostname e non sostituire la URL fornita. Non usare Docker, Testcontainers, SQLite o PostgreSQL auto-avviato dal test code.

Se la URL non raggiunge PostgreSQL reale o fallisce i controlli di sicurezza già ratificati, il lavoro non può diventare candidate-ready. Il mero fatto che il nome host sia locale non autorizza né impone uno STOP.

Se una authority frozen è contraddittoria o non determina il comportamento, ferma soltanto il punto interessato e segnala un architecture finding. Non scegliere una semantica dal codice corrente e non modificare documenti frozen per adattarli all’implementazione.

---

## 3. Hard scope boundary

La correzione deve restare **test/evidence-only**.

File ammessi, quando necessari:

```text
tests/support/s08_static.py
tests/support/m2_evidence.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_s08_evidence.py
tests/test_m2_traceability.py
un eventuale helper test-only strettamente necessario
docs/milestones/M2/evidence/README.md
docs/milestones/M2/status.md
```

Non modificare:

```text
src/netauto production code
public API
Health contract
CLI grammar, behavior o rendering
SQLAlchemy metadata
schema o DDL
migration 0001_m2_kernel
Alembic graph
pyproject.toml
uv.lock
src/netauto/release/runtime.pylock.toml
dipendenze
versione 0.2.0
wheel content
public error catalog
operation inventories
```

Non iniziare `M2-S09`.

Non creare:

```text
docs/milestones/M2/acceptance.md
candidate-specific S09 evidence record
PR
GitHub Actions workflow o run
tag
GitHub Release
artifact publication
```

Preserva esattamente:

```text
version                          0.2.0
authoritative tables             15
Alembic bases / heads            1 / 1
head                             0001_m2_kernel
compare_metadata                 []
public business HTTP operations  63
operational Health operations    1
total public HTTP operations     64
CLI remote / local operations    63 / 8
public error codes               23
registry examples                65
canonical scenarios              83
safety predicates                21
negative-surface identifiers     131
```

---

# 4. S08-VRF-05 — Import-time Alembic mutation closure

## 4.1 Difetto

L’analizzatore corrente rileva chiamate mutanti contenute nei corpi delle funzioni raggiungibili, ma può non rilevare esecuzione mutante durante l’import del modulo o la costruzione di una classe.

Devono essere rilevate almeno queste forme:

```python
from alembic.command import upgrade as migrate
migrate(config, "head")
```

```python
from alembic import command as alembic_command

class Runtime:
    state = alembic_command.stamp(config, "head")
```

```python
# sample.server
import sample.adapter

def build_app():
    ...

# sample.adapter
from alembic.command import downgrade as reset_schema
reset_schema(config, "base")
```

Una mutazione import-time è una migrazione automatica e deve fallire l’audit anche se non è invocata da una funzione applicativa.

## 4.2 Comportamento richiesto

Estendi `find_reachable_alembic_mutations()` o l’equivalente helper test-only affinché modelli almeno:

```text
module initialization
class body execution
ordinary function/method execution
```

La closure deve includere:

```text
root module initialization
initialization dei moduli importati dai root
chiamate top-level
chiamate dentro if / try / with / match / loop top-level
corpi di classe eseguibili, escludendo i corpi ordinari dei metodi
class bases, keyword/metaclass expressions e class decorators
function decorators
positional defaults e keyword defaults eseguiti alla definizione
chiamate top-level a helper locali
chiamate class-body a helper locali
wrapper importati e aliasati
```

Rispetta lo scope lessicale:

```text
import dentro funzione != alias del modulo
import dentro metodo != alias del class/module body
alias omonimi in scope diversi restano distinti
```

La risoluzione deve continuare a riconoscere:

```text
from alembic.command import upgrade
from alembic.command import upgrade as migrate
import alembic.command as command
from alembic import command as alembic_command
```

con chiamate:

```text
upgrade(...)
migrate(...)
command.upgrade(...)
alembic_command.upgrade(...)
```

Le sole mutazioni vietate sono:

```text
alembic.command.upgrade
alembic.command.downgrade
alembic.command.stamp
alembic.command.revision
alembic.command.merge
```

L’introspezione non mutante resta ammessa:

```text
Alembic Config
ScriptDirectory
MigrationContext
get_heads
get_current_heads
revision inspection
```

## 4.3 Root reali

Esegui l’audit sulla closure di produzione raggiungibile almeno da:

```text
netauto.entrypoints.http
server/application factory
ASGI lifespan/composition
netauto.runtime e relativi moduli
schema guard
netauto.cli e relativi moduli
console-entrypoint/import path
```

Un modulo amministrativo Alembic non è vietato per il solo fatto di esistere; è finding quando una mutazione è raggiungibile automaticamente dai root runtime/server/CLI o viene eseguita durante il loro import.

## 4.4 Regressioni obbligatorie

Aggiungi test puri e deterministici per:

```text
1. direct top-level alias
2. imported-module side effect
3. class-body side effect
4. import-time call through local helper
5. decorator o default argument che invoca un wrapper mutante
6. introspezione Alembic non mutante con zero finding
7. scope locale che non contamina l’alias map esterna
```

Ogni finding deve fornire diagnostica bounded:

```text
modulo
nodo/funzione o synthetic initialization owner
linea
target mutante risolto
call path comprensibile
```

---

# 5. S08-VRF-06 — Semantic closure delle negative surfaces astratte

## 5.1 Difetto

Il registry contiene 131 entry esatte, ma alcune voci deployment, security, data-protection, availability e observability puntano ancora a un test che non rileverebbe una realizzazione della capability con un nome o una collocazione diversa.

Le entry ad alto rischio includono almeno:

```text
data_protection::PostgreSQL replica management
data_protection::point-in-time recovery procedure
data_protection::business-continuity SLA

deployment_platform::multi-region operation
deployment_platform::service discovery, clustering or high availability
deployment_platform::CI/CD deployment pipeline

security_network::reverse-proxy or firewall automation
security_network::VPN or load-balancer configuration

observability::dashboards or alerting
observability::central log shipping or rotation
```

## 5.2 Comportamento richiesto

Mantieni esattamente:

```text
131 negative-surface identifiers
nessuna entry mancante
nessuna entry extra
ogni entry con almeno un concrete pytest target raccolto
mapping entry-specific
```

Introduci una registry finita o un meccanismo equivalente per le capability astratte che definisca:

```text
superfici repository da ispezionare
path e basename vietati
directory/componenti vietati
moduli production vietati
script/entrypoint vietati
dipendenze vietate
infrastructure/config assets vietati
operator documents vietati quando realizzano la capability
concrete assertion target
synthetic counterexample target
```

L’audit deve ispezionare in modo proporzionato:

```text
git-tracked file/path inventory
production Python module inventory
pyproject dependencies
pyproject scripts/entrypoints
configuration/infrastructure assets
operator/deployment documents non normativi
CI/deployment directories
dashboard/logging/proxy/firewall/recovery assets
```

Non usare un grep globale che fallisca perché il contract frozen descrive esplicitamente un concetto come non-goal.

Le authority normative devono poter contenere frasi come:

```text
no multi-region operation
no backup automation
no metrics integration
```

senza essere interpretate come implementazione della capability.

## 5.3 Controesempi sintetici obbligatori

Il nuovo audit deve rilevare almeno:

```text
docs/operations/business-continuity.md
docs/operations/postgresql-replicas.md
docs/operations/pitr.md
docs/deployment/multi-region.md
docs/deployment/high-availability.md

ops/nginx.conf
ops/firewall-rules.nft
ops/vpn.conf
ops/postgresql-replica.conf

src/netauto/cluster.py
src/netauto/replication.py
src/netauto/backup.py

.circleci/config.yml
dashboards/core.json
grafana/datasources/netauto.yml
fluent-bit.conf
```

Mantieni rilevati anche:

```text
nested Dockerfile
Kubernetes manifests
systemd unit
backup.sh / restore.sh
.github/workflows
```

Aggiungi controesempi sicuri che non devono essere classificati:

```text
docs/milestones/M2/contract.md
docs/milestones/M2/architecture/runtime-deployment.md
docs/architecture/*.md
src/netauto/runtime/schema_guard.py
ordinary test files che descrivono il non-goal
```

## 5.4 Mapping semantico

Per le entry astratte ad alto rischio, `M2_NEGATIVE_SURFACE_TO_TARGETS` deve includere esplicitamente:

```text
target del capability audit finito
synthetic-counterexample target
```

Non è sufficiente:

```text
mapping non vuoto
numero minimo di target-set distinti
un solo test generico che non asserisce la capability
```

È ammesso condividere un target tra entry realmente omogenee soltanto se il target contiene una policy finita che nomina e verifica ciascuna entry.

Aggiorna la traceability affinché verifichi:

```text
exact 131-key census
concrete collected targets
high-risk entries -> dedicated capability audit
nessuna broad-category fallback automatica
nessun target inesistente
nessuna dipendenza da execution prompt o WIP authority
```

---

# 6. S08-VRF-07 — Reviewer `ACCEPTED` coherence

## 6.1 Difetto

La fase reviewer accetta attualmente:

```text
reviewer_decision = ACCEPTED
```

senza verificare che il record rappresenti un final gate interamente passato.

Un record reviewer `ACCEPTED` non può contenere evidenza fallita o bloccata, comandi falliti, finding aperti o SQLSTATE vietati.

## 6.2 Fasi da preservare

```text
implementer
    reviewer_decision deve essere null

reviewer
    reviewer_decision deve essere:
        ACCEPTED
        REVIEW CHANGES REQUIRED
```

## 6.3 Decisione `ACCEPTED`

Richiedi esattamente:

```text
ogni M2-VER-01 ... M2-VER-32 == PASS
ogni scenario canonico 83 / 83 == PASS
ogni safety predicate 21 / 21 == PASS
installed_t9 == PASS
ogni command.exit_status == 0
runtime_census.skipped == 0
runtime_census.xfailed == 0
runtime_census.rerun == 0
runtime_census.supported_40p01 == 0
runtime_census.unexpected_40001 == 0
open_findings == ()
```

Mantieni tutte le validazioni già esistenti:

```text
locked_environment_confirmed
build_confirmed
schema table count 15
one base/head/current revision 0001_m2_kernel
compare_metadata == ()
operation census 63 / 1 / 63 / 8 / 65
valid hashes
safe secret-free record
```

Una warning terza parte censita può essere non-zero; non introdurre arbitrariamente `warnings == 0`.

## 6.4 Decisione `REVIEW CHANGES REQUIRED`

Il record può contenere:

```text
FAIL
BLOCKED
command exit non-zero
finding aperti
SQLSTATE o gate non conformi
```

ma deve comunque rispettare:

```text
schema del record
exact identifier sets
valori non negativi
safe serialization
no secret / DB URL / DSN / userinfo
finite reviewer-decision vocabulary
```

Non richiedere artificialmente che almeno un campo sia `FAIL`: il reviewer può avere un finding qualitativo non ancora materializzato in un test result.

## 6.5 Regressioni obbligatorie

Verifica che un record completo e coerente con `ACCEPTED` sia valido.

Verifica separatamente che `ACCEPTED` venga rifiutato quando è presente:

```text
1. un evidence bundle FAIL
2. uno scenario BLOCKED
3. un predicate non PASS
4. installed_t9 non PASS
5. un command exit_status = 1
6. open_findings non vuoto
7. runtime skipped > 0
8. runtime xfailed > 0
9. runtime rerun > 0
10. supported_40p01 > 0
11. unexpected_40001 > 0
```

Per ciascuna mutazione verifica che lo stesso record con:

```text
reviewer_decision = REVIEW CHANGES REQUIRED
```

resti validabile nella fase reviewer.

Mantieni le regressioni già presenti per:

```text
implementer che tenta di impostare reviewer_decision
decisione fuori vocabolario
HTTP/HTTPS endpoint senza userinfo ammesso
PostgreSQL URL vietato
DSN vietato
HTTP/HTTPS userinfo vietato
secret-bearing value vietato
stable deterministic JSON
```

---

# 7. Traceability permanente del review-fix

Crea o estendi:

```text
S08_REVIEW_FIX_TARGETS
```

Il registry deve contenere esattamente:

```text
S08-VRF-01
S08-VRF-02
S08-VRF-03
S08-VRF-04
S08-VRF-05
S08-VRF-06
S08-VRF-07
```

Preserva i target dei primi quattro finding e aggiungi target concreti per gli ultimi tre.

Machine-check:

```text
exact seven-key census
ogni finding ha target non vuoti
ogni target esiste ed è raccolto
S08-VRF-05 include import-time/module/class-body tests
S08-VRF-06 include capability-audit e synthetic counterexamples
S08-VRF-07 include acceptance-coherence tests
```

Aggiorna, quando necessario, la membership di:

```text
M2-VER-31
M2-VER-32
```

senza rimuovere target precedentemente accettati.

Entrambi devono restare:

```text
IMPLEMENTED
non-empty
concretely collected
```

## WIP lifecycle

Il prompt S08 originale è superseded e deve essere assente:

```text
docs/milestones/M2/wip/M2-S08-codex-prompt.md
```

Il WIP census deve trattare soltanto questo review-fix prompt come execution aid attivo opzionale:

```text
docs/milestones/M2/wip/M2-S08-review-fixes-codex-prompt.md
```

Il test deve passare:

```text
mentre il prompt è presente durante il review-fix
dopo la futura rimozione reviewer-owned all’acceptance
```

Preserva esattamente i 19 documenti storici classificati e i due closure record permanenti.

---

# 8. Verification

Esegui prima i target focused dei tre finding.

Registra:

```text
selected targets
unique targets
parametrized pass count
duration
```

## 8.1 Quality e pre-flight

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

## 8.2 Focused review-fix

```text
tutti i target S08-VRF-05
tutti i target S08-VRF-06
tutti i target S08-VRF-07
S08_REVIEW_FIX_TARGETS registry test
prompt-present e prompt-absent WIP lifecycle tests
PTY reverse-search target
```

## 8.3 S08 bundles e T10

```text
M2-VER-31 complete deduplicated union
M2-VER-32 complete deduplicated union
tutti i test S08/T10
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py
direct union dei 51 scenari consegnati
```

## 8.4 Previous-slice preservation

```text
S06 completo
S07/T9 completo
API/error/CLI equality group
schema/Alembic positive and negative group
runtime/schema-guard/Health group
```

## 8.5 Integrated

```text
PostgreSQL/concurrency suite completa
non-PostgreSQL suite completa
repository suite completa
```

Usa soltanto il `TEST_DATABASE_URL` esplicitamente fornito.

Non usare:

```text
Docker
Testcontainers
SQLite
hostname o credenziali inventati
automatic retry per nascondere failure
xdist su PostgreSQL interferente senza isolamento esistente
```

Gate obbligatori:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATE        exact finite expected census
schema drift                     []
new unexplained warnings         0
```

La deprecazione Starlette/FastAPI già censita può restare l’unica warning.

---

# 9. Candidate publication

Se un gate obbligatorio fallisce:

```text
mantieni M2-S08 IN PROGRESS
mantieni M2-S09 BLOCKED
correggi soltanto dentro il perimetro S08
non consegnare un candidate
```

Se tutti i gate passano:

1. aggiorna `status.md` a:

```text
M2-S08    CANDIDATE READY FOR REVIEW
M2-S09    BLOCKED
```

Non impostare mai `M2-S08 COMPLETED`.

2. registra nello status:

```text
starting ancestry
review-fix commit
candidate evidence/status commit
chiusura S08-VRF-05 / 06 / 07
exact seven-finding registry
VER-31 selected / unique / passed
VER-32 selected / unique / passed
S08/T10 e traceability
51 delivered scenarios
S06
S07/T9
API/error/CLI
schema/Alembic
PostgreSQL/concurrency
non-PostgreSQL
full repository
collection
quality/build
skip/xfail/rerun/warning/SQLSTATE censuses
PostgreSQL version realmente osservata
artifact hash invariato
production/schema/API/CLI/dependency boundaries invariati
```

3. committa e pusha esclusivamente su `M2`.

Separazione consigliata:

```text
test(m2): close remaining S08 verification findings
docs(m2): publish final corrected S08 candidate evidence
```

4. verifica:

```text
HEAD == origin/M2 == remote M2
ahead / behind == 0 / 0
working tree pulito
```

5. sull’esatto nuovo remote HEAD riesegui almeno:

```text
focused S08-VRF-05/06/07
S08_REVIEW_FIX_TARGETS
M2-VER-31
M2-VER-32
S08/T10 + traceability
51 delivered scenarios
S06 completo
S07/T9
API/error/CLI
schema/Alembic
PostgreSQL/concurrency
non-PostgreSQL
full repository
```

Se qualunque post-push gate fallisce:

```text
torna a M2-S08 IN PROGRESS
mantieni M2-S09 BLOCKED
non consegnare il candidate
```

Non creare un candidate-specific record sotto `docs/milestones/M2/evidence/`; appartiene a S09.

---

# 10. Final report

Riporta soltanto fatti verificati:

```text
branch
starting ancestry
reviewer reopen ancestry
review-fix commit
evidence/status commit
final remote HEAD
HEAD/origin/remote equality
ahead/behind
clean worktree

files changed
S08-VRF-05 closure
S08-VRF-06 closure
S08-VRF-07 closure
exact S08_REVIEW_FIX_TARGETS census

VER-31 result
VER-32 result
S08/T10 result
51-scenario result
S06 result
S07/T9 result
PostgreSQL result
non-PostgreSQL result
full-suite result

collection
Ruff/Pyright/build
skip/xfail/rerun
warning census
SQLSTATE census
compare_metadata result
PostgreSQL version osservata

unchanged production/API/CLI/schema/migration/dependencies/locks
absence of PR/Actions/tag/Release/artifact publication
M2-S09 BLOCKED
```

L’unico handoff implementer ammesso è:

```text
M2-S08    CANDIDATE READY FOR REVIEW
M2-S09    BLOCKED
```

Non dichiarare:

```text
M2-S08 COMPLETED
M2-S09 iniziata
M2 DELIVERED
final acceptance
```
