# syntax=docker/dockerfile:1

FROM python:3.11 as base

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update && \
    apt install -y \
    curl \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    libtiff-dev \
    libjpeg-dev \
    libfreetype-dev \
    liblcms-dev \
    libwebp-dev \
    tcl-dev \
    tk-dev \
    espeak-ng
RUN curl -sSL https://install.python-poetry.org | python3 -

RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:/root/.local/bin:$PATH"

WORKDIR /chapter-sync

COPY pyproject.toml poetry.lock .
RUN --mount=type=cache,target=/root/.cache/pypoetry poetry install --only main --no-root

COPY . .
RUN --mount=type=cache,target=/root/.cache/pypoetry poetry install --only-root

FROM python:3.11 as final
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update && mkdir /data

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV DATABASE_NAME=/data/chapter-sync.sqlite

COPY --from=base /opt/venv /opt/venv

WORKDIR /chapter-sync
COPY . .

ENTRYPOINT ["chapter-sync"]
CMD ["watch"]
