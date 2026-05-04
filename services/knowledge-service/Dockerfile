FROM python:3.11-slim

WORKDIR /app

# Copy requirements first so Docker can cache dependency installation.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code.
COPY src/ ./src/

EXPOSE 8005

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]
