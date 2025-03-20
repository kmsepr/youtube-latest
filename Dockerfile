# Use the latest official Python image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN pip install --no-cache-dir yt-dlp flask

# Copy all application files
COPY . .

# Expose port 8000 for the Flask app
EXPOSE 8000

# Run the Flask app
CMD ["python", "server.py"]