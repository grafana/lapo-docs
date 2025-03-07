FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/

RUN apt update && apt install -y git

WORKDIR /app

COPY uv.lock .
COPY pyproject.toml .

RUN uv sync --frozen

COPY . .

ENTRYPOINT ["./entrypoint.sh"]
