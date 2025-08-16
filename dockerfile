# syntax=docker/dockerfile:1.7
FROM python:3.9-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv once; cached as a separate layer
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv

# Copy only requirements for a stable cache key
COPY requirements.txt .

# Fast, cached dependency install via BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# Now copy the rest of the source
COPY . .

CMD ["python", "main.py"]