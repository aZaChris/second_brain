# Research: STT e Captioning Locali in Pipeline

Nessun `[NEEDS CLARIFICATION]` residuo.

## Libreria e modello STT

**Decision**: `faster-whisper` con il modello `base` (multilingue, supporta l'italiano),
quantizzazione `int8` per l'inferenza CPU.

**Rationale**: è il nome esplicitamente citato dal testo della feature e coerente con
`faster-whisper` essendo un motore CTranslate2 ottimizzato per CPU (più veloce di
`openai-whisper`/PyTorch a parità di modello, senza dipendenza da `torch`). Il modello `base`
bilancia accuratezza e velocità per note vocali personali brevi — `tiny` sarebbe più veloce ma con
qualità di trascrizione sensibilmente peggiore per l'italiano; `small`/`medium` più accurati ma più
lenti su CPU, oltre il budget per un uso interattivo.

**Alternatives considered**: `openai-whisper` (libreria di riferimento originale, PyTorch-based) —
scartata: più lenta su CPU a parità di modello e aggiungerebbe una seconda dipendenza pesante da
`torch` oltre a quella già introdotta per il captioning, senza un beneficio di qualità
sufficiente a giustificarlo. Modello `tiny` — scartato, qualità di trascuzione italiana troppo
bassa per un caso d'uso di note personali che poi finiscono nella ricerca semantica di `core`.

## Libreria e modello di captioning

**Decision**: `transformers` con `Salesforce/blip-image-captioning-base` (BLIP, ~990MB).

**Rationale**: modello consolidato, ampiamente usato per image captioning generico, buon
compromesso dimensione/qualità per didascalie descrittive di foto personali (non serve
riconoscimento specializzato). Usare `transformers` (già una dipendenza indiretta forte
nell'ecosistema Python per questo genere di modelli) invece di una libreria dedicata aggiuntiva
mantiene una sola libreria di inferenza per entrambi i compiti visione/testo del progetto (stesso
ecosistema di `sentence-transformers` in `core`, che internamente usa anch'esso `transformers`).

**Alternatives considered**: modelli VLM più recenti e più capaci (es. `moondream2`) — scartati,
più pesanti e pensati per compiti più complessi delle semplici didascalie descrittive che questo
sistema richiede (FR-002 non richiede comprensione visiva sofisticata, solo una descrizione
testuale). `nlpconnect/vit-gpt2-image-captioning` (più piccolo, ~1GB anch'esso) — alternativa
comparabile, non scelta solo per popolarità/manutenzione più recente di BLIP.

**Correzione post-implementazione**: il primo tentativo usava `transformers.pipeline("image-to-text",
...)`, l'astrazione generica a task. Fallito in test reale: la versione di `transformers`
installata (5.15.1) non ha più il task `"image-to-text"` nel registro (`KeyError`, task
disponibili non lo includono più). Corretto usando le classi BLIP dedicate
(`BlipProcessor`/`BlipForConditionalGeneration`, `from_pretrained` + `generate` +
`processor.decode`), stabili tra versioni perché specifiche del modello invece che
dell'astrazione a task generico.

## Precauzione CPU-only per `torch` (captioning)

**Decision**: stesso fix già applicato in `009-embedding-locale-core` — installare `torch`
esplicitamente dalla build CPU (`pip install torch --index-url
https://download.pytorch.org/whl/cpu`) in un passo `RUN` dedicato del `Dockerfile`, prima di
`pip install -r requirements.txt`.

**Rationale**: senza questo passo, `pip install -r requirements.txt` risolverebbe la build CUDA
di `torch` per `transformers`/BLIP, stesso problema già misurato in `009-embedding-locale-core`
(venv da poche centinaia di MB a 5.1GB con librerie `nvidia-*` inutili su un nodo senza GPU).
`faster-whisper` non necessita di questo fix: usa `ctranslate2`, che non porta con sé le stesse
dipendenze CUDA per la build CPU standard da PyPI.

**Alternatives considered**: nessuna — è una correzione già validata, non una nuova decisione da
soppesare.

## Caricamento dei modelli

**Decision**: `preload(config)` in `pipeline/src/worker.py`, chiamato una sola volta in `main()`
prima di entrare nel loop `while True: run_once(...)`, analogo a `core/src/main.py` in
`009-embedding-locale-core`. Carica entrambi i modelli (STT e captioning) se le rispettive
modalità sono `"local"`.

**Rationale**: FR-004 richiede caricamento una sola volta all'avvio, non per richiesta. A
differenza di `core` (FastAPI, dove serve distinguere `create_app()` usato dai test da `main.py`
usato in produzione), `pipeline` non ha un equivalente `create_app()` testato in isolamento: i test
di `worker.py` chiamano direttamente `process_event()`/`run_once()` con `transcribe`/`caption`
mockati, quindi non c'è rischio di innescare un caricamento reale del modello nei test già
esistenti — comunque, `preload()` resta una funzione separata da `main()` per poterla non chiamare
esplicitamente nei nuovi unit test di `transcription.py`/`captioning.py`.

**Alternatives considered**: lazy loading al primo file processato — scartato per lo stesso motivo
già documentato in `009-embedding-locale-core` (sposterebbe il costo sul primo evento reale invece
che sull'avvio).

## Cache dei pesi

**Decision**: due sottocartelle dentro l'unico bind mount già definito
(`models-cache/pipeline:/models` da `008-docker-deployment`): `/models/stt` (passata come
`download_root` a `WhisperModel`) e `/models/captioning` (passata come `cache_dir` al caricamento
di BLIP via `transformers`).

**Rationale**: un solo volume già esiste per `pipeline` (niente da aggiungere ai file Docker),
sottocartelle separate evitano collisioni tra le convenzioni di cache diverse delle due librerie
(CTranslate2 vs Hugging Face Hub).

**Alternatives considered**: due volumi Docker separati — scartato, non necessario: sono due
sottocartelle dello stesso mount, non due dispositivi/percorsi fisici diversi.

## Modalità esterna come fallback, indipendente per audio/immagine (FR-006)

**Decision**: due variabili indipendenti, `STT_MODE` e `CAPTIONING_MODE` (`local` di default
ciascuna), lette da `pipeline/src/config.py`. `transcribe()`/`caption()` accettano `config` invece
dei parametri sciolti `api_url`/`api_token`/`max_retries`/`backoff_seconds` (quei parametri restano
usati solo internamente da `_transcribe_external`/`_caption_external`, letti da `config` quando la
modalità è `external`).

**Rationale**: stesso pattern già validato in `009-embedding-locale-core` per `embed()`; qui in
più serve indipendenza tra audio e immagini (FR-006 lo richiede esplicitamente: si può restare
locali per l'STT e passare a un servizio esterno solo per il captioning, o viceversa, senza dover
scegliere in blocco).

**Alternatives considered**: un'unica variabile `PIPELINE_MODE` per entrambi — scartata, non
soddisferebbe FR-006 (le due capacità devono poter avere qualità/tempi diversi e quindi
configurazioni indipendenti).

## Condivisione di risorse tra i due modelli nello stesso processo

**Decision**: nessuna modifica ai limiti `cpus`/`mem_limit` già assegnati a `pipeline` da
`008-docker-deployment`; entrambi i modelli restano caricati in memoria contemporaneamente, ma
l'inferenza resta sequenziale (il worker elabora un evento alla volta in `run_once`, mai STT e
captioning in parallelo nello stesso processo).

**Rationale**: `worker.py` già processa gli eventi in un ciclo sequenziale (`for event in
events: process_event(...)`) — nessuna concorrenza interna da gestire. Il costo di memoria è la
somma dei due modelli caricati (STT `base` + BLIP-base, ordine di 1-1.5GB insieme), da validare
contro il `mem_limit` di `pipeline/docker-compose.yml` (4g, impostato in `008-docker-deployment`)
in fase di implementazione — se insufficiente, aumentare quel valore è un aggiustamento di
configurazione, non un cambiamento a questa feature.

**Alternatives considered**: caricare i modelli lazy, uno alla volta, scaricando quello non in uso
per risparmiare memoria — scartato, contraddice FR-004 (caricamento una sola volta all'avvio) e
introdurrebbe latenza di ricaricamento ad ogni cambio di tipo di evento.
