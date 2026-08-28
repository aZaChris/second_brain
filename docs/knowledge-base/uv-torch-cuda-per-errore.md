# KB: `uv` risolve `torch` come build CUDA se non si forza l'indice CPU

## Sintomo

Passando le venv di `core`/`pipeline` da `pip` a `uv` (per condividere su disco i pacchetti
identici tra moduli, vedi `docs/knowledge-base/`), `core/.venv` è passata da 1.4G a **4.9G** dopo
`uv pip install -r requirements-dev.txt`.

## Causa radice

Il `Dockerfile` di `core`/`pipeline` installa `torch` in un passo separato, **prima** del resto:

```dockerfile
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
```

Questo passo non è documentato da nessuna parte fuori dal `Dockerfile` — non in
`requirements.txt`, non nei README. Eseguendo `uv pip install -r requirements-dev.txt` senza
replicarlo, `uv` ha risolto `torch` con l'indice PyPI di default, che per `torch` è la build CUDA:
GB di pacchetti `nvidia-*` (`cublas`, `cudnn`, `cufft`, `nccl`, ...) e `triton` (compilatore JIT
CUDA), tutti inutili su un nodo senza GPU.

**Effetto collaterale scoperto nello stesso momento**: `pipeline` non ha proprio installato
`torch`. `transformers` non lo dichiara come dipendenza rigida (supporta più backend), quindi
senza il passo esplicito del Dockerfile `uv` non lo installa affatto — `captioning.py`, che usa
BLIP via `transformers`, sarebbe crashato al primo uso reale (i test lo mascherano: mockano il
modello, non lo importano mai davvero).

## Come l'abbiamo confermata

```bash
core/.venv/bin/pip show torch   # Version: 2.13.0 (senza +cpu) invece di 2.13.0+cpu
du -sh core/.venv/lib/python3.12/site-packages/nvidia   # 2.7G
```

## Risoluzione

1. Ricreate le venv da zero, installando `torch` CPU-only **esplicitamente prima** del resto,
   stesso ordine del `Dockerfile`:
   ```bash
   uv pip install --python core/.venv torch --index-url https://download.pytorch.org/whl/cpu
   uv pip install --python core/.venv -r core/requirements-dev.txt
   ```
2. Verificato che `core` e `pipeline` condividessero lo stesso file fisico (non solo la stessa
   versione) via hard link:
   ```bash
   stat -c '%i' core/.venv/.../torch/_C.cpython-312-x86_64-linux-gnu.so
   stat -c '%i' pipeline/.venv/.../torch/_C.cpython-312-x86_64-linux-gnu.so
   # stesso inode → confermato
   ```
3. `uv cache prune` non è bastato a liberare i pacchetti CUDA scaricati per errore (rimossi solo
   1.5G su 7.4G di cache) — serviva `uv cache clean` (wipe completo, 4.5G rimossi). Gli hard link
   già creati nelle venv sopravvivono comunque alla cache svuotata (semantica POSIX: un hard link
   non dipende dal file "originale").

Risultato finale: disco totale usato sul sistema sceso sotto il livello di partenza (17.76GB →
16.17GB), nonostante l'errore intermedio.

## Lezione per il futuro

Se il `Dockerfile` forza un indice/versione specifica per evitare bloat (GPU, architettura,
piattaforma...), quel vincolo va replicato esplicitamente in **ogni** strumento di installazione
usato in locale — non è qualcosa che `pip`/`uv` deducono da soli leggendo `requirements.txt`.
Meglio ancora: documentarlo nel README del modulo, non solo nel `Dockerfile` (vedi
[`readme-env-var-obsolete.md`](readme-env-var-obsolete.md), stesso principio — la documentazione
di setup locale va tenuta in sync con le decisioni prese altrove).

## Riferimenti

- `core/Dockerfile`, `pipeline/Dockerfile` (passo `torch --index-url .../whl/cpu`)
- `specs/009-embedding-locale-core/research.md` (motivazione originale del fix CPU-only)
