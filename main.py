import subprocess
import os
import time
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

# Paths
COOKIES_PATH = "/mnt/data/cookies.txt"
VIDEO_PATH = "/mnt/data/latest_video.mp4"
AUDIO_PATH = "/mnt/data/latest_audio.mp3"

# Ensure yt-dlp & ffmpeg are installed
subprocess.run(["pip", "install", "--no-cache-dir", "-U", "yt-dlp", "flask"])

def download_latest_video(channel_url):
    """Downloads the latest video from the channel."""
    try:
        # yt-dlp command to get latest video URL
        command = [
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--no-playlist",
            "-f", "best",
            "-o", VIDEO_PATH,
            channel_url
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def convert_video_to_audio():
    """Converts the downloaded video to audio using FFmpeg."""
    try:
        command = [
            "ffmpeg",
            "-y",  # Overwrite output file if exists
            "-i", VIDEO_PATH,
            "-vn",  # No video
            "-acodec", "mp3",
            AUDIO_PATH
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@app.route('/stream', methods=['GET'])
def stream_audio():
    """Fetches the latest video, converts it, and streams as audio."""
    channel_url = request.args.get("channel")
    if not channel_url:
        return jsonify({"error": "Channel URL is required"}), 400

    # Download & convert
    if download_latest_video(channel_url) is not True:
        return jsonify({"error": "Failed to download video"}), 500
    if convert_video_to_audio() is not True:
        return jsonify({"error": "Failed to convert video to audio"}), 500

    # Stream the audio file
    def generate_audio():
        with open(AUDIO_PATH, "rb") as f:
            while chunk := f.read(1024):
                yield chunk

    return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)