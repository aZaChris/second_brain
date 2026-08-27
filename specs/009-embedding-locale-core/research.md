# Research: Embedding Locale in Core

Nessun `[NEEDS CLARIFICATION]` residuo.

## Libreria e modello

**Decision**: `sentence-transformers` con il modello
`paraphrase-multilingual-MiniLM-L12-v2` (384 dimensioni, ~470MB, supporta l'italiano).

**Rationale**: è il nome esplicitamente citato sia dal `research.md` originale di
`002-core-similarity-engine` sia dal Principio IV della constitution v2.0.0 — coerenza con la
decisione già presa a livello di principio, non una scelta nuova da giustificare da zero. Il
modello `paraphrase-multilingual-MiniLM-L12-v2` è pensato per analogia semantica generica
(paraphrase/STS), lo stesso caso d'uso di `find_similar` (confronto simmetrico testo-contro-testo
già salvato) — nessuna convenzione di prefisso `query:`/`passage:` da gestire, a differenza dei
modelli orientati al retrieval asimmetrico (es. `multilingual-e5-small`), che avrebbe richiesto
codice aggiuntivo in `embedding.py` senza un beneficio per questo caso d'uso.

**Alternatives considered**: `fastembed` (ONNX runtime, senza dipendenza da `torch`) — libreria
più leggera e più veloce in inferenza CPU pura, scartata solo perché il Principio IV della
constitution nomina già esplicitamente `sentence-transformers`; resta un'alternativa valida da
rivalutare se le dimensioni dell'immagine Docker di `core` (che cresce sensibilmente con `torch`)
risultassero un problema concreto in pratica. `multilingual-e5-small` — scartato per la
convenzione di prefisso non necessaria a un confronto simmetrico.

## Caricamento del modello

**Decision**: caricamento eager a livello di modulo in `core/src/embedding.py` (variabile
module-level, istanziata all'import del modulo), stesso pattern già usato in `core/src/main.py`
per `Config.from_env()`.

**Rationale**: FR-003 richiede che il modello sia caricato una sola volta all'avvio, non per
richiesta — un singleton a livello di modulo, popolato all'import (che avviene una sola volta per
processo), lo garantisce senza bisogno di lazy-loading con lock per la concorrenza.

**Alternatives considered**: lazy loading al primo utilizzo — scartato, sposterebbe il costo del
caricamento sulla prima richiesta reale invece che sull'avvio del processo, rendendo il primo
evento visibilmente più lento senza un beneficio (il processo non fa altro di utile prima di poter
generare embedding).

## Cache dei pesi

**Decision**: variabile d'ambiente `EMBEDDING_MODEL_CACHE` puntata a `/models` (il bind mount di
`008-docker-deployment`), passata come `cache_folder` al costruttore di `SentenceTransformer`.

**Rationale**: soddisfa FR-004/SC-003 riusando l'infrastruttura già predisposta dalla feature
Docker, senza introdurre un nuovo meccanismo di cache.

**Alternatives considered**: cache di default di `sentence-transformers`
(`~/.cache/torch/sentence_transformers`) dentro il filesystem effimero del container — scartata,
richiederebbe un ri-download dei pesi (centinaia di MB) ad ogni ricreazione del container,
violando SC-003.

## Modalità esterna come fallback (FR-005)

**Decision**: nuova variabile `EMBEDDING_MODE` (`local` di default, `external` per il fallback);
`embed()` accetta l'oggetto `config` e decide internamente quale percorso usare, invece dei
parametri sciolti `api_url`/`api_token` di oggi.

**Rationale**: il testo utente della feature chiede che l'interfaccia `embed(text) -> list[float]`
resti "invariata verso similarity.py/api.py" — verificato che `similarity.py`/`insight.py` non
referenziano mai `embed()` direttamente (solo `api.py` lo chiama), quindi il vincolo si traduce
in: nessun cambiamento a `similarity.py`/`insight.py` (rispettato), e in `api.py` un adattamento
meccanico dei 2 punti di chiamata (passano `config` invece di `api_url`/`api_token` sciolti) per
poter esprimere la scelta locale/esterno in modo configurabile — trade-off esplicito, documentato
qui invece di forzare un'interfaccia identica che nasconderebbe la nuova modalità dentro
`Config` stesso (meno leggibile).

**Alternatives considered**: mantenere la firma `embed(text, *, api_url, api_token)` anche in
modalità locale, ignorando i parametri quando `EMBEDDING_MODE=local` — scartato, firma fuorviante
(parametri obbligatori che non servono quasi mai) e comunque non elimina la necessità di leggere
`EMBEDDING_MODE` da qualche parte in `api.py`.

## Formato dei vettori esistenti (FR-006)

**Decision**: `find_similar` (in `similarity.py`, non toccato da questa feature) confronta solo
embedding della stessa dimensionalità di quello appena generato; eventuali embedding con
dimensionalità diversa (es. residui di un vecchio provider esterno) vengono esclusi dal confronto
invece di causare un errore.

**Rationale**: FR-006 richiede di non rompere la ricerca in presenza di vettori incompatibili;
escluderli è la modifica più piccola che soddisfa il requisito, senza introdurre una migrazione
dati (fuori scope, vedi Assumptions di spec.md).

**Alternatives considered**: rigenerare automaticamente al volo gli embedding con dimensionalità
sbagliata — scartato, introdurrebbe un side-effect silenzioso e un costo di calcolo imprevedibile
durante una ricerca; una rigenerazione esplicita resta un'attività operativa separata (one-off),
non un comportamento implicito del codice.

## Immagine Docker più pesante

**Decision**: accettare la crescita dell'immagine `core` dovuta a `torch` CPU (centinaia di MB in
più), senza multi-stage build dedicato per ora — ma installare esplicitamente la build CPU-only
di `torch` (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) prima di
`pip install -r requirements.txt`, in un passo `RUN` dedicato nel `Dockerfile`.

**Correzione post-implementazione**: il primo tentativo (`pip install -r requirements.txt` senza
questo passo) ha risolto la build CUDA di default di `torch`, portando il venv da poche centinaia
di MB a **5.1GB** (librerie `nvidia-*`/`triton`/`cuda-toolkit` completamente inutili su un nodo
senza GPU — violazione diretta dei Vincoli Tecnici della constitution, "nessuna GPU assunta
disponibile"). Installare `torch` CPU-only per primo lo fissa come "già soddisfatto" per pip, che
poi non lo tocca risolvendo `sentence-transformers`: venv sceso a 1.4GB. Verificato con
`torch.cuda.is_available() == False` e nessun pacchetto `nvidia-*`/`triton` installato.

**Rationale**: lo storage SATA del nodo ZimaBlade non è un vincolo stringente (a differenza della
microSD del Pi); il tempo di build una tantum non è un costo ricorrente. Ottimizzare le dimensioni
dell'immagine ora sarebbe ottimizzazione prematura senza un problema misurato.

**Alternatives considered**: `fastembed`/ONNX per un'immagine più leggera — vedi sopra
("Libreria e modello"), stessa conclusione: rimandato a quando/se le dimensioni diventano un
problema concreto.
