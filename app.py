import os
import subprocess
import time
import threading
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
stream_cache = {}  # Stores the latest audio URL per station
failed_videos = set()  # Tracks failed video URLs
cache_lock = threading.Lock()

def get_playlist_videos(playlist_id):
    """Fetch videos from a YouTube playlist and return the latest one."""
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=1&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            print(f"API Error: {data['error']['message']}")
            return None

        if "items" in data and data["items"]:
            return f"https://www.youtube.com/watch?v={data['items'][0]['snippet']['resourceId']['videoId']}"

    except Exception as e:
        print(f"Error fetching playlist videos: {e}")

    return None

def extract_audio_url(video_url, retries=3):
    """Extract direct audio URL using yt-dlp."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "-f", "bestaudio",
        "-g", video_url
    ]

    for attempt in range(retries):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            audio_url = result.stdout.strip()
            if audio_url:
                return audio_url
        except subprocess.CalledProcessError:
            print(f"yt-dlp failed for {video_url}, attempt {attempt + 1}")
        time.sleep(2)

    failed_videos.add(video_url)
    return None

def refresh_stream_urls():
    """Refresh the audio URLs every 30 minutes."""
    while True:
        with cache_lock:
            for station, playlist_id in YOUTUBE_PLAYLISTS.items():
                latest_video = get_playlist_videos(playlist_id)

                if not latest_video or latest_video in failed_videos:
                    print(f"No valid video for {station}, skipping...")
                    continue

                audio_url = extract_audio_url(latest_video)

                if audio_url:
                    stream_cache[station] = audio_url
                    print(f"Updated cache for {station}: {audio_url}")

        time.sleep(1800)  # Refresh every 30 minutes

def generate_stream(station_name):
    """Continuously stream audio from the cached URL."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        if not stream_url:
            print(f"No valid stream URL for {station_name}, retrying in 10s...")
            time.sleep(10)
            continue

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", stream_url,
             "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1",
             "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except Exception:
            process.kill()
            print(f"Stream failed for {station_name}, retrying in 5 seconds...")
            time.sleep(5)

@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in YOUTUBE_PLAYLISTS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

# Start the background refresh thread
threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)