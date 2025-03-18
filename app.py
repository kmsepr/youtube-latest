from flask import Flask, Response, jsonify
import subprocess
import os
import threading

app = Flask(__name__)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"
COOKIES_FILE = "/mnt/data/cookies.txt"
cache_lock = threading.Lock()
latest_video_url = None
latest_audio_url = None

# Function to get the latest video from the playlist
def get_latest_video():
    global latest_video_url

    try:
        command = ["yt-dlp", "--flat-playlist", "-i", "--print", "%(url)s", YOUTUBE_PLAYLIST]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        video_urls = result.stdout.strip().split("\n")
        if video_urls:
            latest_video_url = video_urls[0]  # The first one is the latest
            print(f"✅ Latest video URL: {latest_video_url}")
        else:
            print("⚠️ No videos found in the playlist.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error getting latest video: {e}")
        latest_video_url = None

# Function to get the audio URL (M4A format)
def get_audio_url():
    global latest_audio_url

    if not latest_video_url:
        get_latest_video()

    if not latest_video_url:
        print("⚠️ No valid latest video URL found.")
        return None

    try:
        command = [
            "yt-dlp",
            "--cookies", COOKIES_FILE,
            "-f", "140",  # Ensuring M4A format
            "-g", latest_video_url
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        latest_audio_url = result.stdout.strip()
        print(f"✅ Latest audio URL: {latest_audio_url}")
        return latest_audio_url
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error getting audio URL: {e}")
        return None

# Stream audio
def generate_audio():
    audio_url = get_audio_url()
    if not audio_url:
        print("⚠️ No audio URL available for streaming.")
        return

    command = ["ffmpeg", "-re", "-i", audio_url, "-c", "copy", "-f", "mp3", "-"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        for chunk in iter(lambda: process.stdout.read(4096), b""):
            yield chunk
    except GeneratorExit:
        process.terminate()
    except Exception as e:
        print(f"⚠️ Error during audio streaming: {e}")

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/refresh')
def refresh():
    get_latest_video()
    return jsonify({"message": "Latest video updated", "video_url": latest_video_url})

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the latest video audio"})

if __name__ == '__main__':
    get_latest_video()
    port = int(os.environ.get("PORT", 8080))  # Default to 8080 if PORT not set
    print(f"🚀 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, threaded=True, debug=True)