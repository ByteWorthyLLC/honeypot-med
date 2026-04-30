FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/honeypot

WORKDIR /app

RUN useradd --create-home --home-dir /home/honeypot --shell /usr/sbin/nologin honeypot

COPY pyproject.toml README.md app.py ./
COPY src ./src
COPY examples ./examples
COPY schemas ./schemas
COPY scripts/docker ./scripts/docker

RUN pip install --no-cache-dir . \
    && chmod +x /app/scripts/docker/entrypoint.sh

USER honeypot

EXPOSE 8899 8787
VOLUME ["/home/honeypot"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python", "/app/scripts/docker/healthcheck.py"]

ENTRYPOINT ["/app/scripts/docker/entrypoint.sh"]
CMD ["studio"]

