FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 7860

# Command with file watching for development
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.fileWatcherType=poll"] 