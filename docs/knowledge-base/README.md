# Knowledge base

Problemi reali incontrati durante lo sviluppo, con diagnosi e risoluzione — non teoria, casi
concreti con i comandi usati per capirci qualcosa.

| Problema | Sintesi |
|---|---|
| [`oom-worker-pipeline.md`](oom-worker-pipeline.md) | Worker `pipeline` morto silenziosamente al preload dei modelli locali: RAM insufficiente nel sandbox di sviluppo (2.6GB), non un bug — l'hardware di destinazione (ZimaBlade, 16GB) non ha questo limite. |
| [`uv-torch-cuda-per-errore.md`](uv-torch-cuda-per-errore.md) | Migrando le venv a `uv`, `torch` è stato risolto come build CUDA (+3.5G di pacchetti `nvidia-*` inutili) perché il vincolo CPU-only del `Dockerfile` non era replicato fuori da esso. |
| [`readme-env-var-obsolete.md`](readme-env-var-obsolete.md) | I README di `core`/`pipeline` proponevano ancora le variabili del vecchio servizio esterno come obbligatorie: seguirli alla lettera faceva crashare l'app, perché il default era ormai `local` (009/010). |
