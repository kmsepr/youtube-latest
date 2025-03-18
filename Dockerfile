# Use a lightweight official Python image
FROM python:3.9-slim-bullseye

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker caching)
COPY requirements.txt .

# Install dependencies (faster builds)
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Install ffmpeg (minimal footprint)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application files
COPY . .

# Expose port 8080 (Koyeb default)
EXPOSE 8080

# Set environment variable for Koyeb
ENV PORT=8080

# Command to run the application
CMD ["python", "app.py"]