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
    "studyiq_recent": "PLMDetQy00TVnZIvklM-3lPLjBmZe2yj7z",
    "vallathoru_katha": "PLLSiSzpILVXmTXgDdM1FXNZVyTz_Nca52",
    "zaytuna_2k25": "PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
    "modern_history": "PLMDetQy00TVleGpEtzwkA0rl6Hkruz9XX",
    "seera_malayalam": "PLEMT7g5NsFuULZoe2U4p8LMYGo2MCFYWt",
    "unacademy_newspaper": "PLJxZBt-LTVo-j3UilMmrcTBxY_U-XS6Ti",
    "entri_ca": "PLYKzjRvMAyciPNzy1YbHWkdweksV5uvbx"
}

# Caches
stream_cache = {}  # Stores latest working audio URLs
failed_videos = set()  # Tracks failed videos
cache_lock = threading.Lock()

def get_playlist_videos(playlist_id):
    """Fetch multiple videos from a YouTube playlist and return the first working one."""
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=5&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                video_id = item["snippet"]["resourceId"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                if video_url not in failed_videos:
                    return video_url

    except Exception as e:
        print(f"Error fetching playlist videos: {e}")

    return None

def extract_audio_url(video_url):
    """Extract direct audio URL using yt-dlp."""
    command = [
        "yt-dlp", "--live-from-start",  # Handle live streams properly
        "--cookies", "/mnt/data/cookies.txt",
        "-f", "bestaudio",
        "-g", video_url
    ]
    print(f"Running yt-dlp for: {video_url}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        if audio_url:
            print(f"Extracted URL: {audio_url}")
            return audio_url
        else:
            print(f"yt-dlp returned empty output for {video_url}")

    except subprocess.CalledProcessError as e:
        print(f"Failed to extract audio: {e}")

    failed_videos.add(video_url)
    return None

def refresh_stream_urls():
    """Refresh the audio URLs every 8 minutes to prevent looping."""
    while True:
        with cache_lock:
            for station, playlist_id in YOUTUBE_PLAYLISTS.items():
                latest_video = get_playlist_videos(playlist_id)

                if not latest_video or latest_video in failed_videos:
                    print(f"No valid video for {station}, skipping...")
                    continue

                audio_url = extract_audio_url(latest_video)

                if audio_url:
                    stream_cache[station] = audio_url  # Store only the latest video's audio URL
                    print(f"Updated cache for {station}: {audio_url}")

        time.sleep(480)  # Refresh every 8 minutes (480 seconds)

def generate_stream(station_name):
    """Continuously stream audio and refresh when looping is detected."""
    last_audio_url = None
    last_fetch_time = time.time()

    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        # Refresh URL every 8 minutes to prevent looping
        if not stream_url or (time.time() - last_fetch_time > 480):  # 480s = 8 min
            print(f"Refreshing stream URL for {station_name}...")
            latest_video = get_playlist_videos(YOUTUBE_PLAYLISTS[station_name])
            if latest_video:
                stream_url = extract_audio_url(latest_video)
                if stream_url:
                    with cache_lock:
                        stream_cache[station_name] = stream_url
                    last_audio_url = stream_url
                    last_fetch_time = time.time()

        if not stream_url:
            print(f"Still no valid stream URL for {station_name}, retrying in 10s...")
            time.sleep(10)
            continue

        print(f"Streaming from: {stream_url}")

        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-http_persistent", "0",  # Fix for YouTube disconnections
                "-i", stream_url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except (GeneratorExit, Exception):
            print(f"Stream error for {station_name}, restarting stream...")
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