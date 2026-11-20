FROM ghcr.io/astral-sh/uv:0.9.10 AS uv
FROM python:3.13-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib IPYTHONDIR=/tmp/ipython \
    JUPYTER_DATA_DIR=/tmp/jupyter JUPYTER_RUNTIME_DIR=/tmp/jupyter-runtime \
    PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY eda ./eda
COPY validation ./validation
COPY modeling ./modeling
COPY data/raw ./data/raw
COPY __main__.py ./
COPY README.md ./
RUN uv sync --locked --no-dev

ARG OUTPUT_DIR=/output
ARG SAVE=all
ENV OUTPUT_DIR=${OUTPUT_DIR} SAVE=${SAVE}
ENTRYPOINT ["python", "/app/__main__.py"]
