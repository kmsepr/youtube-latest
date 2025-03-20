FROM python:3.9

# Install FFmpeg
RUN apt update && apt install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "app.py"]