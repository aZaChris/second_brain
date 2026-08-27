# Contratto: struttura minima di un `docker-compose.yml` di modulo

Ogni modulo (`ingestion`, `pipeline`, `core`, `graph`, `companion`) espone il proprio deploy
tramite un `docker-compose.yml` che DEVE rispettare questa struttura, così che l'operatore possa
trattare ogni modulo allo stesso modo indipendentemente da quale sta gestendo (FR-001, FR-007).

## Chiavi obbligatorie per servizio

```yaml
services:
  <nome-modulo>:
    build: .                        # Dockerfile nella stessa cartella
    container_name: second-brain-<nome-modulo>
    env_file: .env                  # mai committato, stesso schema di DEPLOY.md
    restart: unless-stopped | on-failure   # per ruolo, vedi research.md
    networks:
      - second-brain-net

networks:
  second-brain-net:
    external: true                  # creata una volta, fuori da questo file
```

## Chiavi condizionali

- **`ports:`** — solo per `core` (8000), `graph` (8001), `companion` (8002); assente per
  `ingestion` e `pipeline` (non espongono un server HTTP). Pubblicata solo su interfaccia di rete
  locale, mai `0.0.0.0` verso l'esterno della LAN.
- **`volumes:`** — bind mount espliciti verso `/srv/second-brain/...` (vedi `data-model.md`);
  assente per i moduli senza stato persistente (`ingestion`, `companion`).
- **`cpus:` / `mem_limit:`** — obbligatorie per `pipeline` (FR-005); assenti per gli altri moduli
  (nessun limite giustificato dalla spec per loro).

## Cosa NON deve comparire

- Nessun segreto o token in chiaro nel `docker-compose.yml` o nel `Dockerfile` — solo riferimenti
  a `env_file` (FR-006, SC-003).
- Nessuna sezione `deploy.resources.limits` — vedi `research.md` (non affidabile fuori da swarm).
- Nessun riferimento a `localhost`/IP hardcoded per raggiungere un altro modulo — solo nome
  servizio sulla rete condivisa (FR-002).

## Verifica del contratto

Per ciascun modulo, `docker compose config` (validazione statica del file) DEVE risolversi senza
errori, e il servizio dichiarato DEVE comparire nella rete `second-brain-net` una volta avviato
(`docker network inspect second-brain-net`).
