FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend/__init__.py ./backend/__init__.py
RUN --mount=type=cache,target=/root/.cache/pip pip install ".[ui]"

COPY backend ./backend
COPY data ./data
COPY streamlit_app.py ./streamlit_app.py

EXPOSE 8000 8501

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
