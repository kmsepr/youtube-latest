from flask import Flask, Response
import subprocess

app = Flask(__name__)

# Set YouTube channel URL (Change this)
CHANNEL_URL = "https://www.youtube.com/@BBCNews"

# Function to get the latest audio stream URL
def get_latest_audio_url():
    try:
        command = [
            "yt-dlp",
            "--get-url",
            "-f", "bestaudio",
            "--no-playlist",
            CHANNEL_URL
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

# Streaming route
@app.route('/stream')
def stream_audio():
    audio_url = get_latest_audio_url()
    if not audio_url:
        return "Failed to fetch audio stream", 500

    # FFmpeg command to stream audio over HTTP
    command = [
        "ffmpeg",
        "-i", audio_url,
        "-vn", "-acodec", "libmp3lame", "-b:a", "128k",
        "-f", "mp3", "pipe:1"
    ]

    def generate():
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            yield chunk
        process.stdout.close()
        process.wait()

    return Response(generate(), mimetype="audio/mpeg")

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)