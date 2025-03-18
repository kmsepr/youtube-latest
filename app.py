from flask import Flask, Response, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import subprocess
import os
import threading

app = Flask(__name__)

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]  # Default limit for all routes
)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"
COOKIES_FILE = "/mnt/data/cookies.txt"
cache_lock = threading.Lock()
latest_video_url = None
latest_audio_url = None

def get_latest_video():
    global latest_video_url
    command = ["yt-dlp", "--flat-playlist", "-i", "--print", "%(url)s", YOUTUBE_PLAYLIST]
    result = subprocess.run(command, capture_output=True, text=True)
    video_urls = result.stdout.strip().split("\n")
    if video_urls:
        latest_video_url = video_urls[0]

def get_audio_url():
    global latest_audio_url
    if not latest_video_url:
        get_latest_video()
    if not latest_video_url:
        return None
    command = ["yt-dlp", "--cookies", COOKIES_FILE, "-f", "140", "-g", latest_video_url]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        latest_audio_url = result.stdout.strip()
        return latest_audio_url
    except subprocess.CalledProcessError:
        return None

def generate_audio():
    audio_url = get_audio_url()
    if not audio_url:
        return
    command = ["ffmpeg", "-re", "-i", audio_url, "-c", "copy", "-f", "mp3", "-"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        for chunk in iter(lambda: process.stdout.read(4096), b""):
            yield chunk
    except GeneratorExit:
        process.terminate()
    except Exception as e:
        print(f"⚠️ Error: {e}")

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/refresh')
@limiter.limit("2 per minute")  # Limit to 2 requests per minute per IP
def refresh():
    get_latest_video()
    return jsonify({"message": "Latest video updated", "video_url": latest_video_url})

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the latest video audio"})

if __name__ == '__main__':
    get_latest_video()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)