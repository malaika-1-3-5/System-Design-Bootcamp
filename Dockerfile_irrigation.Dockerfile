FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY  irrigation.py ./app/irrigation.py


EXPOSE 8000

CMD ["uvicorn", "app.irrigation:app", "--host", "0.0.0.0", "--port", "8000"]