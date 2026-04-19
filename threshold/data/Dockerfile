FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/data

COPY data /app/data

CMD ["python", "run_all_ingestion.py"]
