import os
import subprocess
import time
import threading
import random
import requests
from flask import Flask, Response, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)

# Station-to-playlist mapping
YOUTUBE_PLAYLISTS = {
    "entri_app": "PL4pF7EMEu-ScQdLg_sFdMKAtYX5xX-Ec1",
    "vallathoru_katha": "PLLSiSzpILVXmTXgDdM1FXNZVyTz_Nca52",
    "zaytuna_2k25": "PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
    "modern_history": "PLMDetQy00TVleGpEtzwkA0rl6Hkruz9XX",
    "seera_malayalam": "PLEMT7g5NsFuULZoe2U4p8LMYGo2MCFYWt"
}

# Caches
stream_cache = {}  # Stores multiple URLs per station
failed_videos = set()  # Tracks failed video URLs to avoid
cache_lock = threading.Lock()

def get_playlist_videos(playlist_id):
    """Fetch videos from a YouTube playlist, ordered by newest first."""
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=10&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            video_items = data["items"]

            # Sort videos by published date (if available)
            video_items.sort(key=lambda x: x["snippet"].get("publishedAt", ""), reverse=True)

            # Extract video URLs
            video_urls = [f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}" for item in video_items]
            return video_urls

    except Exception as e:
        print(f"Error fetching playlist videos: {e}")

    return None

def extract_audio_url(video_url):
    """Extract direct audio URL using yt-dlp."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "-f", "bestaudio",
        "-g", video_url
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        return audio_url if audio_url else None
    except subprocess.CalledProcessError:
        print(f"Failed to extract audio for: {video_url}")
        failed_videos.add(video_url)  # Add to failed list
        return None

def refresh_stream_urls():
    """Refresh the audio URLs every 30 minutes."""
    while True:
        with cache_lock:
            for station, playlist_id in YOUTUBE_PLAYLISTS.items():
                video_urls = get_playlist_videos(playlist_id)
                if video_urls:
                    # Remove failed videos from selection
                    video_urls = [v for v in video_urls if v not in failed_videos]

                    if not video_urls:
                        print(f"No valid videos left for {station}, skipping...")
                        continue

                    latest_video = video_urls[0]  # Newest video first
                    remaining_videos = video_urls[1:]  # The rest of the videos
                    random.shuffle(remaining_videos)  # Shuffle others

                    # Keep a list of multiple URLs for quick switching
                    ordered_videos = [latest_video] + remaining_videos[:4]  # Keep 5 videos
                    audio_urls = [extract_audio_url(v) for v in ordered_videos if v]

                    if audio_urls:
                        stream_cache[station] = audio_urls  # Save multiple URLs
                        print(f"Updated cache for {station}: {audio_urls}")

        time.sleep(1800)  # Refresh every 30 minutes

def generate_stream(station_name):
    """Continuously stream audio from a cached list of URLs."""
    while True:
        with cache_lock:
            stream_urls = stream_cache.get(station_name, [])

        if not stream_urls:
            print(f"No valid stream URLs for {station_name}, fetching new ones...")
            refresh_stream_urls()
            time.sleep(10)
            continue

        for stream_url in stream_urls:
            print(f"Streaming from: {stream_url}")

process = subprocess.Popen(
    ["ffmpeg", "-re", "-i", stream_url,
     "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1",  # Force mono (-ac 1)
     "-f", "mp3", "-"],
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
)

try:
for chunk in iter(lambda: process.stdout.read(8192), b""):
                    yield chunk
            except (GeneratorExit, Exception):
                print(f"Stream error for {station_name}, switching source...")
                process.kill()
                time.sleep(5)
                continue

@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in YOUTUBE_PLAYLISTS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

# Start the background refresh thread
threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)