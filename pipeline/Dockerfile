FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# torch (dipendenza di transformers/BLIP) va installato CPU-only esplicitamente prima del resto:
# senza questo passo pip risolverebbe la build CUDA di default (vedi
# specs/009-embedding-locale-core/research.md — stesso fix, stesso motivo). faster-whisper usa
# ctranslate2, che non ha questo problema.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

RUN useradd --create-home appuser \
    && mkdir -p /models/stt /models/captioning \
    && chown -R appuser:appuser /models
USER appuser

CMD ["python", "-m", "src.worker"]
