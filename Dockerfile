FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system knowledge && useradd --system --gid knowledge --home-dir /app knowledge

COPY --chown=knowledge:knowledge . /app
RUN python -m pip install --upgrade pip && python -m pip install .

USER knowledge
EXPOSE 8000

CMD ["knowledge", "--root", "/app", "web", "--host", "0.0.0.0", "--port", "8000"]
