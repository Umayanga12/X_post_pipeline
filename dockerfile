# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_MODEL=hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

# Run the app
CMD ["python", "main.py"]
