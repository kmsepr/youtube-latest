# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Upgrade pip before installing dependencies
RUN pip install --upgrade pip

# Copy the application files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for the Flask server
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]