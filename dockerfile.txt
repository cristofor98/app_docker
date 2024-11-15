# Use Python base image
FROM python:3.9-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose ports for Flask and WebSocket
EXPOSE 5000 8001

# Command to run the application
CMD ["python", "app.py"]