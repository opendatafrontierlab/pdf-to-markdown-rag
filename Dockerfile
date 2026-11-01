FROM apify/actor-python:3.13
COPY --chown=myuser:myuser requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=myuser:myuser . ./
# Warm up: build a 1-page image-only PDF and OCR it, so RapidOCR models are baked into the image.
RUN python -m src.warmup || true
RUN python -m compileall -q src/
CMD ["python3", "-m", "src"]
