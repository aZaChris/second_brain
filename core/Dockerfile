# numpy ha ruote precompilate per cp312/manylinux x86_64: pip le usa direttamente,
# nessun toolchain di compilazione necessario nell'immagine (research.md).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# torch va installato CPU-only esplicitamente prima del resto: senza questo passo, pip
# risolverebbe la build CUDA di default (diversi GB di librerie nvidia inutili su un nodo senza
# GPU, vedi Vincoli Tecnici della constitution) — installandolo qui, `pip install -r
# requirements.txt` lo trova già soddisfatto e non lo tocca (specs/009-embedding-locale-core/).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

RUN useradd --create-home appuser && mkdir -p /data /models && chown appuser:appuser /data /models
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
