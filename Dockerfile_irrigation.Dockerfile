FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY  irrigation.py .
COPY processor.py .
COPY ingestion.py .
COPY irrigation_service.py .

CMD ["python", "processor.py"]