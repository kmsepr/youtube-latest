import os
import subprocess
import time
import threading
import requests
from flask import Flask, Response, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Flask app setup
app = Flask(__name__)

# Mapping of channel names to YouTube Channel IDs
YOUTUBE_CHANNELS = {
    "entri_app": "UC9VKXPGzRIs9raMlCwzljtA",
    "media_one": "UC-f7r46JhYv78q5pGrO6ivA"
}

# Cache to store the latest audio URLs
stream_cache = {}
cache_lock = threading.Lock()

def get_latest_video_url(channel_id):
    """Fetch the latest video URL from a YouTube channel using the YouTube API."""
    url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"].get("videoId")
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        print(f"Error fetching latest video: {e}")

    return None

def get_audio_url(video_url):
    """Extract the direct audio URL from a YouTube video using yt-dlp."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",  # Using cookies.txt for authentication
        "-f", "bestaudio",
        "-g", video_url
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        return audio_url if audio_url else None
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio URL: {e}")
        return None

def refresh_stream_url():
    """Refresh audio stream URLs every 30 minutes."""
    while True:
        with cache_lock:
            for station, channel_id in YOUTUBE_CHANNELS.items():
                video_url = get_latest_video_url(channel_id)
                if video_url:
                    audio_url = get_audio_url(video_url)
                    if audio_url:
                        stream_cache[station] = audio_url
                        print(f"Updated stream URL for {station}: {audio_url}")

        time.sleep(1800)  # Refresh every 30 minutes

def generate_stream(station_name):
    """Stream audio using FFmpeg."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        if not stream_url:
            print(f"No valid stream URL for {station_name}, fetching a new one...")
            with cache_lock:
                channel_id = YOUTUBE_CHANNELS.get(station_name)
                if channel_id:
                    video_url = get_latest_video_url(channel_id)
                    if video_url:
                        stream_url = get_audio_url(video_url)
                        if stream_url:
                            stream_cache[station_name] = stream_url

        if not stream_url:
            print(f"Failed to fetch stream URL for {station_name}, retrying in 30s...")
            time.sleep(30)
            continue

        print(f"Streaming from: {stream_url}")

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", stream_url,
             "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "2",
             "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except (GeneratorExit, Exception):
            print(f"Stream error for {station_name}, restarting...")
            process.kill()
            time.sleep(5)
            continue

@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in YOUTUBE_CHANNELS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

# Start the URL refresher thread
threading.Thread(target=refresh_stream_url, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)