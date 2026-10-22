FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser backend/app ./backend/app
COPY --chown=appuser:appuser datasets/mock_project.json ./datasets/mock_project.json
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
