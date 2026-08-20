# Codex review-fix prompt — M2-S08 package-aware relative imports

**Status:** NON-NORMATIVE IMPLEMENTATION EXECUTION AID.

Questo file autorizza esclusivamente la continuazione correttiva di:

```text
M2-S08 — Integrated regression, traceability and negative-surface closure
```

È subordinato a `AGENTS.md`, all’AS-IS consegnato, al contract e all’architecture set M2 `FINAL / FROZEN`, a `steps.md`, alla technology baseline ratificata e allo stato reviewer-owned in `status.md`.

Il presente contenuto sostituisce il precedente aid S08 nello stesso path. Il path resta l’unico execution aid attivo ammesso dal censimento WIP; non creare un secondo prompt.

---

## 1. Assignment e baseline

Lavora direttamente sul branch:

```text
M2
```

Candidate rifiutato e baseline di ancestry obbligatoria:

```text
c4cd4e633afaafa395a67f2b9efcc396906052e1
docs(m2): publish S08 candidate after PTY closure
```

Reviewer-owned reopen obbligatorio nell’ancestry:

```text
620b3016f4ef66eab53831125cc21d879edb5ac5
docs(m2): reopen S08 for package-relative import closure
```

Queste SHA sono baseline di ancestry, non l’HEAD esatto atteso: la pubblicazione di questo aid crea necessariamente un commit successivo.

Correggi esclusivamente la parte ancora aperta di:

```text
S08-VRF-05
    package-aware relative-import closure
    nell’audit delle mutazioni Alembic import-time
```

Non creare un nuovo finding. Il registro deve restare esattamente:

```text
S08-VRF-01
S08-VRF-02
S08-VRF-03
S08-VRF-04
S08-VRF-05
S08-VRF-06
S08-VRF-07
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

S08-VRF-06
    finite abstract-negative capability audit

S08-VRF-07
    reviewer ACCEPTED all-pass coherence

package-parent initializer chain
    già implementata in 29e47eca66667b0e8ba8aefea410476d6dd0710f

S06 PTY reverse-search proof
    già corretta in 954fd86f576f3b4a0ec4efb8849cf059c801dfef
```

Non ripartire da zero. Non eseguire reset, rebase, force-push o riscrittura della cronologia.

Preserva nell’ancestry almeno:

```text
29e47eca66667b0e8ba8aefea410476d6dd0710f
954fd86f576f3b4a0ec4efb8849cf059c801dfef
c4cd4e633afaafa395a67f2b9efcc396906052e1
620b3016f4ef66eab53831125cc21d879edb5ac5
```

---

## 2. Mandatory pre-flight

Prima di modificare file, verifica:

```text
git branch --show-current              M2
HEAD == origin/M2                      sì
working tree                            pulito
origin/M2 contiene c4cd4e6...          sì
origin/M2 contiene 620b301...          sì
questo prompt esiste all’HEAD           sì
M2-S08                                  REVIEW CHANGES REQUIRED o IN PROGRESS
M2-S09                                  BLOCKED
contract                                FINAL / FROZEN
architecture set                        FINAL / FROZEN
steps                                   FINAL / FROZEN
reopen architetturali aperti            nessuno
```

Se `status.md` non autorizza S08 o se M2-S09 non è `BLOCKED`, fermati senza modificare file.

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
docs/milestones/M2/steps.md
docs/milestones/M2/status.md

docs/milestones/M2/wip/M2-S08-review-fixes-codex-prompt.md
```

Ispeziona inoltre:

```text
tests/support/s08_static.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_traceability.py
tests/test_m2_s06_process.py
```

### `TEST_DATABASE_URL`

`TEST_DATABASE_URL` è externally supplied quando è fornito esplicitamente dall’ambiente e il test code NETAUTO non lo provisiona, non lo inventa e non lo sostituisce silenziosamente.

Un hostname loopback o locale non è, da solo, un blocker.

Devi verificare concretamente che:

```text
URL                              presente
forma supportata                 postgresql+psycopg
server raggiungibile             sì
backend reale                    PostgreSQL
versione PostgreSQL              rilevata dalla connessione reale
target test dedicato/sicuro      conforme ai controlli esistenti
provisioning da test code        assente
fallback SQLite/fake             assente
```

Non inventare credenziali o hostname e non sostituire la URL fornita. Non usare Docker, Testcontainers, SQLite o PostgreSQL auto-avviato dal test code.

---

## 3. Hard scope boundary

La correzione deve restare test-only.

File ammessi, quando necessari:

```text
tests/support/s08_static.py
tests/test_m2_s08_negative_surface.py
tests/test_m2_traceability.py
docs/milestones/M2/status.md
```

Non modificare questo execution aid durante l’implementazione.

Non modificare:

```text
src/netauto production code
public API
Health contract
CLI grammar, behavior o rendering
tests/test_m2_s06_process.py
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
evidence schema
negative-capability policies
public error catalog
operation inventories
```

Non iniziare `M2-S09`.

Non creare:

```text
docs/milestones/M2/acceptance.md
candidate-specific S09 evidence record
un secondo execution aid WIP
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

## 4. Difetto da chiudere

### 4.1 Rappresentazione corrente

La production source inventory rappresenta un package initializer eliminando il segmento `__init__`:

```text
src/sample/__init__.py
    -> module name "sample"

src/sample/api/__init__.py
    -> module name "sample.api"
```

Il solo nome del modulo non consente di distinguere:

```text
sample.api.py
    ordinary module

sample/api/__init__.py
    package initializer
```

### 4.2 Risoluzione corrente errata

La funzione equivalente a:

```text
_absolute_import(module, imported, level)
```

calcola sempre il package context come il parent del module name.

Questa regola è corretta per un ordinary module:

```text
module       sample.api.http
__package__  sample.api
```

ma è errata per un package initializer:

```text
module       sample.api
source       sample/api/__init__.py
__package__  sample.api
```

Per un package initializer, il package context è il module name stesso.

### 4.3 Falsi negativi obbligatori da eliminare

Caso root package:

```text
sample/__init__.py
    from . import migrator

sample/migrator.py
    from alembic.command import upgrade
    upgrade(None, "head")
```

Risoluzione Python corretta:

```text
from . import migrator
    -> sample.migrator
```

Caso nested package:

```text
sample/api/__init__.py
    from .. import migrator

sample/migrator.py
    from alembic.command import stamp
    stamp(None, "head")
```

Risoluzione Python corretta:

```text
from .. import migrator
    -> sample.migrator
```

La helper corrente può invece risolvere entrambe come un top-level `migrator`, perdendo l’edge verso il modulo realmente presente.

### 4.4 Superfici coinvolte

La correzione deve applicarsi sia a:

```text
import-edge resolution
    _ExecutionScanner.visit_ImportFrom o equivalente
```

sia a:

```text
import-alias resolution
    _scoped_import_aliases o equivalente
```

Correggere soltanto gli edge non è sufficiente: wrapper e callable importati relativamente devono continuare a risolversi verso i function keys corretti.

---

## 5. Modello richiesto

### 5.1 Package metadata esplicita

Non inferire package/module status dal numero di segmenti del nome.

Mantieni metadata espliciti e finiti per i moduli che provengono da `__init__.py`.

Una forma raccomandata e backward-compatible è:

```text
find_reachable_alembic_mutations(
    module_sources,
    root_modules,
    *,
    package_modules=(),
)
```

con:

```text
package_modules <= module_sources.keys()
```

È ammessa un’equivalente struttura `ModuleSource(source, is_package)`, purché non renda più fragile o ambiguo il test support e resti test-only.

La funzione deve rifiutare package names sconosciuti con un errore deterministico, analogamente agli unknown roots.

### 5.2 Production inventory

La real production inventory deve derivare la package metadata dal path fisico prima di rimuovere `__init__` dal module name:

```text
path.name == "__init__.py"
    -> module is package

altro file .py
    -> ordinary module
```

Preserva una singola source authority. Non creare due mappe divergenti con nomi calcolati in modi differenti.

Puoi:

```text
aggiungere _production_package_modules()
```

oppure:

```text
aggiungere _production_module_inventory()
    -> sources + package_modules
```

ma il real repository audit deve passare esplicitamente la package metadata all’analizzatore.

### 5.3 Package context

Per un ordinary module:

```text
package context = parent del module name
```

Per un package initializer:

```text
package context = module name stesso
```

La risoluzione relativa di livello `level` deve rimuovere `level - 1` segmenti dal package context.

Esempi esatti:

```text
ordinary module sample.api.http
    from . import sibling
        -> sample.api.sibling

    from .. import sibling
        -> sample.sibling

package initializer sample.api
    from . import sibling
        -> sample.api.sibling

    from .. import sibling
        -> sample.sibling
```

### 5.4 Import oltre il top-level

Non trasformare un import relativo oltre il top-level in un import top-level plausibile.

Esempio:

```text
package initializer sample
    from .. import migrator
```

è invalido e non deve diventare:

```text
migrator
```

La helper può restituire `None` o un altro risultato esplicitamente unresolved. I caller devono evitare di creare edge o alias inventati.

### 5.5 Forme da preservare

Preserva la risoluzione di:

```text
import a.b.c
import a.b.c as alias
from a.b import c
from . import c
from .sub import c
from .. import c
from ..sub import c
from alembic.command import upgrade as migrate
from alembic import command as alembic_command
```

Preserva inoltre:

```text
module initialization
class-body execution
function-body execution
definition-time decorator/default calls
local and imported wrappers
lexical alias scope
existing package-parent initializer chain
cycle termination
finding deduplication
bounded eight-element diagnostic path
```

Le sole mutazioni vietate restano:

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

---

## 6. Regressioni obbligatorie

Aggiungi test puri e deterministici in:

```text
tests/test_m2_s08_negative_surface.py
```

Usa nomi stabili equivalenti ai seguenti.

### 6.1 Root package `from . import ...`

```text
test_import_time_alembic_analysis_resolves_relative_import_from_root_package
```

Source inventory:

```text
sample                         package initializer
sample.entry                   ordinary root module
sample.migrator                ordinary module con import-time upgrade
```

`sample/__init__.py` contiene:

```text
from . import migrator
```

Root:

```text
sample.entry
```

Assert:

```text
un solo finding
module      sample.migrator
owner       sample.migrator.<module_init>
target      alembic.command.upgrade
call path   bounded e raggiungibile dal package initializer
```

### 6.2 Nested package `from .. import ...`

```text
test_import_time_alembic_analysis_resolves_parent_relative_import_from_nested_package
```

Source inventory:

```text
sample                         package initializer safe
sample.api                     package initializer
sample.api.http                ordinary root module
sample.migrator                ordinary module con import-time stamp
```

`sample/api/__init__.py` contiene:

```text
from .. import migrator
```

Root:

```text
sample.api.http
```

Assert:

```text
un solo finding in sample.migrator.<module_init>
target alembic.command.stamp
```

### 6.3 Ordinary-module semantics preservata

```text
test_import_time_alembic_analysis_preserves_relative_import_from_ordinary_module
```

Source inventory:

```text
sample                         package
sample.api                     package
sample.api.http                ordinary module
sample.api.sibling             ordinary module con import-time downgrade
```

`sample.api.http` contiene:

```text
from . import sibling
```

Assert:

```text
sample.api.sibling risolto
non sample.api.http.sibling
non sample.sibling
```

### 6.4 Relative imported wrapper

```text
test_import_time_alembic_analysis_resolves_relative_wrapper_from_package
```

Source inventory:

```text
sample                         package initializer
sample.helper                  ordinary module
```

`sample/__init__.py` contiene una forma equivalente a:

```text
from .helper import migrate
migrate()
```

`sample.helper.migrate` invoca una mutazione Alembic vietata.

Assert:

```text
la alias map risolve sample.helper.migrate
il call graph raggiunge il wrapper
il finding mostra il target Alembic mutante
```

### 6.5 Beyond-top-level non inventato

```text
test_import_time_alembic_analysis_does_not_invent_top_level_import_beyond_package
```

Source inventory:

```text
sample                         package initializer
sample.entry                   ordinary root module
migrator                       top-level module con mutazione Alembic
```

`sample/__init__.py` contiene:

```text
from .. import migrator
```

Assert:

```text
nessun edge inventato verso top-level migrator
nessun finding derivato da quell’import invalido
nessun crash
```

### 6.6 Safe package-relative imports

```text
test_import_time_alembic_analysis_accepts_safe_package_relative_imports
```

Copri almeno:

```text
from . import sibling
from .. import sibling
from .submodule import helper
```

con package metadata esplicita e nessuna mutazione. Risultato:

```text
findings == ()
```

### 6.7 Production inventory metadata

```text
test_real_netauto_inventory_marks_exact_package_initializers
```

Verifica almeno:

```text
netauto                         package
netauto.entrypoints             package
netauto.cli                     package
netauto.runtime                 package, se rappresentato da __init__.py
netauto.entrypoints.http        ordinary module
netauto.cli.repl                ordinary module
```

Non hardcodare un package che non esiste fisicamente. Deriva l’atteso dai path reali e asserisci i casi rappresentativi presenti.

Il real production audit deve restare:

```text
find_reachable_alembic_mutations(
    real_sources,
    execution_roots,
    package_modules=real_packages,
) == ()
```

### 6.8 Regressioni precedenti

Mantieni verdi e immutati i target già accettati per:

```text
direct top-level alias
imported-module side effect
class-body side effect
local helper
definition-time wrapper
lexical scope isolation
package-parent initializer chain
missing namespace initializer
cycle termination
real NETAUTO root initializer chains
Alembic introspection only
S06 PTY split sentinel
S06 Ctrl-R structured recall
```

---

## 7. Traceability

Mantieni:

```text
set(S08_REVIEW_FIX_TARGETS)
    == {
        S08-VRF-01,
        S08-VRF-02,
        S08-VRF-03,
        S08-VRF-04,
        S08-VRF-05,
        S08-VRF-06,
        S08-VRF-07,
    }
```

Non aggiungere `S08-VRF-08`.

Aggiungi i nuovi package-aware relative-import target a:

```text
S08_REVIEW_FIX_TARGETS["S08-VRF-05"]
```

Aggiorna:

```text
test_s08_review_fix_registry_is_exact_resolvable_and_bundle_mapped
```

affinché richieda esplicitamente almeno:

```text
root package relative-import target
nested package parent-relative target
ordinary-module preservation target
relative wrapper target
```

Tutti i target devono:

```text
esistere
essere raccolti da pytest
essere inclusi nel review-fix union
appartenere a M2-VER-32
```

Non rimuovere alcun target S08 già accettato.

`M2-VER-31` deve restare invariato, `IMPLEMENTED` e non vuoto.

`M2-VER-32` deve includere sia i target precedenti sia quelli nuovi.

---

## 8. Focused verification

Esegui prima:

```text
nuovi package-relative import test
intero S08-VRF-05
S08 review-fix registry target
real runtime/server/CLI Alembic audit
```

Registra:

```text
target selezionati
target unici
pass parametrizzati
durata
```

Non usare retry automatici.

Esegui quindi:

```text
uv lock --check
uv sync --locked
uv build
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest --collect-only -q
```

---

## 9. Integrated verification

Esegui almeno:

```text
S08_REVIEW_FIX_TARGETS completo
M2-VER-31 complete deduplicated union
M2-VER-32 complete deduplicated union
tutti i test S08/T10
tests/test_m1_traceability.py
tests/test_m2_s00_traceability.py
tests/test_m2_traceability.py

direct union dei 51 scenari consegnati

S06 completo
S07/T9 completo
API/error/CLI group
schema/Alembic positive and negative group
runtime/schema-guard/Health group

PostgreSQL/concurrency suite
non-PostgreSQL suite
repository suite completa
```

Usa esclusivamente il `TEST_DATABASE_URL` esterno già verificato.

Gate obbligatori:

```text
skip / xfail / rerun             0 / 0 / 0
supported-path 40P01             0
unexpected 40001                 0
negative-control SQLSTATE        exact expected census
compare_metadata                 []
new unexplained warnings         0
```

La deprecazione Starlette/FastAPI già censita può restare l’unica warning.

---

## 10. Artifact invariance

Poiché la correzione è test-only, verifica che l’artifact resti invariato:

```text
version               0.2.0
wheel                  netauto-0.2.0-py3-none-any.whl
wheel size             165978 byte
wheel members          77
wheel SHA-256          38f03612583f9b0d72f0de5a44637abf3181d3193ba445b841919753c0ad2c60

runtime lock size      48238 byte
runtime lock SHA-256   0114d64cb078cfe3271e974d4aad86628d633d0fbdbcbece37ff3bc8873ddaaf
```

Se la wheel o il runtime lock cambiano, fermati e identifica il motivo. Una correzione test-only non deve alterare il prodotto distribuito.

Rimuovi `dist/`, wheel, sdist e output temporanei dopo la verifica.

---

## 11. Candidate publication

Se un gate obbligatorio fallisce:

```text
mantieni M2-S08 IN PROGRESS
mantieni M2-S09 BLOCKED
non pubblicare un candidate
```

Se tutti i gate passano, usa preferibilmente due commit:

```text
test(m2): close S08 package-relative import audit

docs(m2): publish relative-import corrected S08 candidate
```

Non usare:

```text
git add .
git add -A
git add --all
```

Stage soltanto i file autorizzati.

Aggiorna `status.md` a:

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

Registra nello status:

```text
starting ancestry c4cd4e6...
reviewer reopen 620b301...
implementation/test commit
candidate evidence/status commit

package metadata mechanism
relative-import correction
new S08-VRF-05 target census
exact seven-finding registry

focused result
M2-VER-31
M2-VER-32
S08/T10
51 scenari
S06
S07/T9
API/error/CLI
schema/Alembic
runtime/schema-guard/Health
PostgreSQL/concurrency
non-PostgreSQL
full repository

collection
Ruff
Pyright
build
skip/xfail/rerun
warning
SQLSTATE
compare_metadata

PostgreSQL version e database identity senza credenziali
artifact hash invariato
production/API/CLI/schema/migration/dependency/lock invariati
```

Pusha soltanto su `M2`.

Verifica:

```text
HEAD == origin/M2 == remote M2
ahead / behind == 0 / 0
working tree pulito
```

---

## 12. Exact-remote post-push gate

Sull’esatto nuovo remote HEAD riesegui almeno:

```text
nuovi package-relative import test
S08-VRF-05 completo
S08_REVIEW_FIX_TARGETS
M2-VER-31
M2-VER-32
S08/T10 + traceability
51 scenari consegnati
S06 completo
S07/T9 completo
API/error/CLI
schema/Alembic
runtime/schema-guard/Health
PostgreSQL/concurrency
non-PostgreSQL
full repository
Ruff format/lint
Pyright
collection
```

Se qualunque gate post-push fallisce:

```text
riporta M2-S08 a IN PROGRESS
mantieni M2-S09 BLOCKED
non consegnare il candidate
```

Un passaggio isolato successivo non sostituisce un gate exact-remote fallito.

---

## 13. Final report

Riporta soltanto fatti verificati:

```text
branch
starting HEAD
reviewer reopen ancestry
implementation commit
evidence/status commit
final remote HEAD
HEAD/origin/remote equality
ahead/behind
clean worktree

file modificati
package metadata implementation
relative-import semantics
regressioni nuove
S08-VRF-05 target finali
seven-finding registry

focused result
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
compare_metadata

wheel e runtime-lock hash
PostgreSQL version/database/probe
confini invariati
assenza di PR/Action/tag/Release/artifact publication
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
