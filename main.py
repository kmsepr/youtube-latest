from flask import Flask, Response, jsonify
import subprocess

app = Flask(__name__)

# Set your YouTube channel URL
CHANNEL_URL = "https://www.youtube.com/@BBCNews"

# Path to cookies.txt file (Replace this with your actual path)
COOKIES_PATH = "/mnt/data/cookies.txt"

# Function to get the latest audio stream URL using cookies
def get_latest_audio_url():
    try:
        command = [
            "yt-dlp", "--get-url", "-f", "bestaudio", "--no-playlist",
            "--cookies", COOKIES_PATH,  # Use cookies
            CHANNEL_URL
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        url = result.stdout.strip()
        
        if not url:
            raise ValueError("No URL found")
        
        return url
    except Exception as e:
        print(f"Error fetching YouTube URL: {e}")
        return None

# Streaming route
@app.route('/stream')
def stream_audio():
    audio_url = get_latest_audio_url()
    if not audio_url:
        return jsonify({"error": "Failed to fetch audio stream"}), 500

    command = [
        "ffmpeg", "-re", "-i", audio_url, "-vn", "-acodec", "libmp3lame",
        "-b:a", "128k", "-f", "mp3", "pipe:1"
    ]

    def generate():
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            print(f"Error streaming audio: {e}")

    return Response(generate(), mimetype="audio/mpeg")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)