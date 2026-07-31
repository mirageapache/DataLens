FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# 先裝依賴（利用 layer cache，改程式碼不會重裝）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

EXPOSE 8000
CMD ["uv", "run", "fastapi", "dev", "app/main.py", "--host", "0.0.0.0"]
