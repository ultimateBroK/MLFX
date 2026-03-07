# --- build stage ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system build dependencies (TA-Lib requires native libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential wget && \
    wget -q https://github.com/TA-Lib/ta-lib/releases/download/v0.4.28/ta-lib-0.4.28-src.tar.gz && \
    tar -xzf ta-lib-0.4.28-src.tar.gz && \
    cd ta-lib && ./configure --prefix=/usr && make -j4 && make install && \
    rm -rf /build/ta-lib*

COPY pyproject.toml README.md ./
COPY mlfx/ ./mlfx/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[serving]" 2>/dev/null || pip install --no-cache-dir .

# --- runtime stage ---
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/lib/libta_lib* /usr/lib/
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY mlfx/ /app/mlfx/

WORKDIR /app

# Data and output volumes
VOLUME ["/app/data", "/app/outputs"]

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "mlfx.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
