# Second Brain

Sistema personale di cattura, indicizzazione e ricerca di appunti/eventi, con Raspberry Pi come nodo di ingestion.

## Moduli

| Modulo | Responsabilità |
|---|---|
| [`ingestion`](ingestion/README.md) | Bot Telegram/WhatsApp: riceve messaggi e li normalizza in eventi |
| [`pipeline`](pipeline/README.md) | Trascrizione audio, captioning immagini |
| [`core`](core/README.md) | Embedding, ricerca per similarità, motore decisionale |
| [`graph`](graph/README.md) | Grafo dei progetti/eventi collegati |
| [`companion`](companion/README.md) | App di consultazione |

Contratto tra moduli: [`API_CONTRACT.md`](API_CONTRACT.md). Stato del progetto: [`CHANGELOG.md`](CHANGELOG.md). Deploy su Raspberry Pi: [`DEPLOY.md`](DEPLOY.md).

## Principi

- Privacy-first: nessuno storage non necessario di dati sensibili.
- Ogni modulo espone un'API chiara, testabile in isolamento.
- Preferenza per servizi esterni (LLM/STT) rispetto a modelli pesanti locali sul Raspberry Pi.

## Branching

- `main` protetto, merge solo via PR.
- Feature branch: `feature/<modulo>-<descrizione>`.
