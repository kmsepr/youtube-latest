# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy the application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y ffmpeg

# Expose port 5000
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
