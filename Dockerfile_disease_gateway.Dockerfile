FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY disease_gateway.py .

EXPOSE 8000

CMD ["uvicorn", "disease_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
