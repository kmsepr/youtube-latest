# Use the official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 5000

# Command to run FastAPI with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]