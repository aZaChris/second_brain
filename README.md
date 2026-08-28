# Second Brain

Sistema personale di cattura, indicizzazione e ricerca di appunti/eventi, containerizzato su un
nodo ZimaBlade (Intel Celeron quad-core x86, 16GB RAM).

## Moduli

| Modulo | Responsabilità |
|---|---|
| [`ingestion`](ingestion/README.md) | Bot Telegram: riceve messaggi e li normalizza in eventi |
| [`pipeline`](pipeline/README.md) | Trascrizione audio e captioning immagini (modelli locali) |
| [`core`](core/README.md) | Embedding (locale), ricerca per similarità, motore decisionale |
| [`graph`](graph/README.md) | Grafo dei progetti/eventi collegati |
| [`companion`](companion/README.md) | App di consultazione (ricerca, esplorazione grafo) |

Contratto tra moduli: [`API_CONTRACT.md`](API_CONTRACT.md). Stato del progetto:
[`CHANGELOG.md`](CHANGELOG.md). Deploy containerizzato: [`DEPLOY.md`](DEPLOY.md). Relazione
completa: [`docs/relazione-progetto.md`](docs/relazione-progetto.md).

## Principi

- Privacy-first: nessuno storage non necessario di dati sensibili.
- Ogni modulo espone un'API chiara, testabile in isolamento.
- Preferenza per modelli locali leggeri (embedding, STT, captioning) rispetto a servizi esterni, su nodo ZimaBlade.

## Branching

- `main` protetto, merge solo via PR.
- Feature branch: `feature/<modulo>-<descrizione>`.
