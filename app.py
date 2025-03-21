import os
import subprocess
import time
import threading
import random
import requests
from flask import Flask, Response, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)

# Mapping of station names to YouTube playlist IDs
YOUTUBE_PLAYLISTS = {
    "entri_app": "PL4pF7EMEu-ScQdLg_sFdMKAtYX5xX-Ec1",
    "media_one": "PLxFIR7FGtGJ9T9zvI3oQGZKQZR1PvBziX"
}

# Cache to store playlist videos
stream_cache = {}
cache_lock = threading.Lock()

def get_playlist_videos(playlist_id):
    """Fetch all video URLs from a YouTube playlist."""
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=10&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            video_urls = [f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}" for item in data["items"]]
            return video_urls
    except Exception as e:
        print(f"Error fetching playlist videos: {e}")

    return None

def extract_audio_url(video_url):
    """Extract the direct audio URL from a YouTube video using yt-dlp."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "--force-generic-extractor",
        "-f", "91",
        "-g", video_url
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        return audio_url if audio_url else None
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio URL: {e}")
        return None

def refresh_stream_urls():
    """Refresh audio stream URLs every 30 minutes by cycling through the playlist."""
    while True:
        with cache_lock:
            for station, playlist_id in YOUTUBE_PLAYLISTS.items():
                video_urls = get_playlist_videos(playlist_id)
                if video_urls:
                    selected_video = random.choice(video_urls)  # Pick a random video from the playlist
                    audio_url = extract_audio_url(selected_video)
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
                playlist_id = YOUTUBE_PLAYLISTS.get(station_name)
                if playlist_id:
                    video_urls = get_playlist_videos(playlist_id)
                    if video_urls:
                        selected_video = random.choice(video_urls)
                        stream_url = extract_audio_url(selected_video)
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
    if station_name not in YOUTUBE_PLAYLISTS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

# Start the URL refresher thread
threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)