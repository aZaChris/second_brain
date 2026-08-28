# KB: `pipeline` muore silenziosamente al preload dei modelli locali (OOM)

## Sintomo

Durante la validazione live di `010-stt-captioning-locale` (STT/captioning locali), il worker
`pipeline` (`python -m src.worker`) veniva avviato in background e spariva senza traccia:

- nessun traceback, nessun messaggio di errore
- il log si fermava dopo il solo warning di autenticazione di Hugging Face Hub
- `ps -p <pid>` non trovava più il processo

Isolando solo `transcription.preload(config)` (più leggero di `captioning.preload`, che carica
anche BLIP via `transformers`), il processo non moriva ma non completava nemmeno entro 120s —
comportamento coerente con thrashing dello swap, non con un crash rapido.

## Ambiente in cui si è manifestato

Sandbox di sviluppo (WSL2 su Windows), **non** l'hardware di destinazione:

```bash
dmesg | grep hv_balloon   # → "Max. dynamic memory size: 2866 MB"
free -h                   # → 2.6Gi totali, swap quasi esaurito
```

L'host fisico sotto WSL2 ha in totale solo **5.6GB di RAM** (verificato da Task Manager di
Windows) — WSL2 ne allocava circa metà (comportamento di default, non un limite artificiale del
sandbox). Il target reale di deploy è tutt'altra storia: ZimaBlade, Celeron quad-core, **16GB RAM**
(`DEPLOY.md`).

## Causa radice

`core` (embedding, `sentence-transformers`) e `pipeline` (`faster-whisper` + `transformers`/BLIP)
caricano ciascuno un modello in RAM al preload, **una sola volta per processo, mai per richiesta**
(pattern deliberato, vedi `specs/009-embedding-locale-core/` e `specs/010-stt-captioning-locale/`
— il pattern in sé è corretto). Il problema non è il codice: è che avviare `core` + `pipeline`
insieme su una macchina con ~2.6GB disponibili non basta a tenere in RAM torch + transformers +
faster-whisper contemporaneamente. Nessun log OOM esplicito del kernel è stato trovato (possibile
kill a livello hypervisor/cgroup, che non sempre logga come OOM standard) — ma il pattern di morte
(sparizione silenziosa, nessun segnale, swap già esaurito) è coerente con un OOM kill.

## Come l'abbiamo confermata

1. Isolato `transcription.preload()` da solo (più leggero) → non crasha ma non completa in 120s.
2. Verificato `free -h`/`dmesg` per i numeri di RAM/swap disponibili nel sandbox.
3. Confrontato con `DEPLOY.md`: il target reale ha 16GB, non 2.6GB — la discrepanza spiega perché
   il codice (già validato da 117 test automatici con modelli mockati) non è il sospetto.

## Risoluzione

Nessun fix nel codice — non c'era nulla da correggere lì. Deciso di:

- lasciare aperti i task che richiedono l'esecuzione live dei modelli in questo sandbox
  (`specs/010-stt-captioning-locale/tasks.md` T011-T013, `specs/009-embedding-locale-core/tasks.md`
  T011), con una nota esplicita del motivo invece di forzare una validazione finta
- riportare il limite onestamente invece di continuare a ritentare alla cieca
- rimandare quella validazione all'hardware reale (ZimaBlade) o a una macchina dev con più RAM

## Quando ricontrollare

Se in futuro serve far girare `core`+`pipeline` insieme per test locali (non solo container
isolati), verificare prima `free -h` sull'host: sotto ~4GB liberi, aspettarsi lo stesso problema.
Su Docker, `pipeline/docker-compose.yml` ha già `mem_limit: "4g"` — un limite esplicito, non una
garanzia che l'host abbia abbastanza margine per tutti e 5 i moduli insieme.

## Riferimenti

- `specs/010-stt-captioning-locale/tasks.md` (T011-T013)
- `specs/009-embedding-locale-core/tasks.md` (T011)
- `DEPLOY.md` (hardware di destinazione, limiti di risorse)
- `pipeline/src/transcription.py`, `pipeline/src/captioning.py` (`preload()`)
