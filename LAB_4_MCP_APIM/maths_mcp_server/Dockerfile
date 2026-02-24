FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application file
COPY server.py .

# Expose the default port
EXPOSE 8001

# Run the server
CMD ["python", "server.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8001"]
