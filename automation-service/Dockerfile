FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPELINE_DOWNLOAD_DIR=/data/downloads

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg tini \
    && rm -rf /var/lib/apt/lists/*

# Copy automation-service package
COPY automation-service/pyproject.toml automation-service/README.md ./automation-service/
COPY automation-service/automation_service ./automation-service/automation_service

# Copy pipeline-run client
COPY pipeline/pyproject.toml pipeline/README.md ./pipeline/
COPY pipeline/pipeline_client ./pipeline/pipeline_client
COPY pipeline/pipeline_runner ./pipeline/pipeline_runner

RUN pip install --upgrade pip \
    && pip install ./pipeline \
    && pip install ./automation-service

RUN mkdir -p /data/downloads

EXPOSE 8000

ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "automation_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
