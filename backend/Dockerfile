FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port that FastAPI runs on
EXPOSE 8000

# Command with reload for development
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 