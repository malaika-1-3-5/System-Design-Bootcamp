FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY disease_detector.py .

CMD ["python", "disease_detector.py"]
