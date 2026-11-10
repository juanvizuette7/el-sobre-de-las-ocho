# Imágenes fijadas por digest para poder repetir esta etapa.
FROM python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b AS base

# Aplica el parche de seguridad disponible sin cambiar la versión de Python ni el resto de la base.
RUN apt-get update \
    && apt-get install --no-install-recommends --yes zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /project
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home portal \
    && mkdir /data && chown portal:portal /data && chmod 700 /data
COPY --chown=portal:portal app ./app

# Las herramientas de prueba no se instalan en la imagen que sirve el portal.
FROM base AS test
COPY requirements-dev.txt pytest.ini ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY --chown=portal:portal tests ./tests
COPY --chown=portal:portal scripts/demo_sql_injection.py ./scripts/demo_sql_injection.py
USER portal
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS runtime
USER portal
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-proxy-headers", "--no-access-log"]
