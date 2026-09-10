FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /ash

COPY ./pyproject.toml ./uv.lock .
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install -r pyproject.toml --system

COPY ./ash /ash/ash
CMD ["python", "-m", "ash"]
