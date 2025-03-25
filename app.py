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

YOUTUBE_PLAYLISTS = {
    "studyiq_recent": "PLMDetQy00TVnZIvklM-3lPLjBmZe2yj7z",
    "vallathoru_katha": "PLLSiSzpILVXmTXgDdM1FXNZVyTz_Nca52",
    "zaytuna_2k25": "PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
    "modern_history": "PLMDetQy00TVleGpEtzwkA0rl6Hkruz9XX",
    "seera_malayalam": "PLEMT7g5NsFuULZoe2U4p8LMYGo2MCFYWt",
    "unacademy_newspaper": "PLJxZBt-LTVo-j3UilMmrcTBxY_U-XS6Ti",
    "entri_ca": "PLYKzjRvMAyciPNzy1YbHWkdweksV5uvbx"
}

stream_cache = {}
failed_videos = set()
cache_lock = threading.Lock()

def get_playlist_videos(playlist_id):
    """Fetch the latest non-live video from a YouTube playlist."""
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=5&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                video_id = item["snippet"]["resourceId"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                if is_live_video(video_id):
                    print(f"Skipping live video: {video_url}")
                    continue

                if video_url not in failed_videos:
                    return video_url

    except Exception as e:
        print(f"Error fetching playlist videos: {e}")

    return None

def is_live_video(video_id):
    """Check if a video is live."""
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,liveStreamingDetails&id={video_id}&key={YOUTUBE_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if "items" in data and len(data["items"]) > 0:
            if "liveStreamingDetails" in data["items"][0]:
                return True
    except Exception as e:
        print(f"Error checking live status: {e}")

    return False

def extract_audio_url(video_url):
    """Extract direct audio URL using yt-dlp."""
    command = [
        "yt-dlp", "--cookies", "/mnt/data/cookies.txt",
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
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract audio: {e}")

    failed_videos.add(video_url)
    return None

def refresh_stream_urls():
    """Refresh stream URLs when needed."""
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

        time.sleep(30)  # Check every 30 seconds if refresh is needed

def detect_looping(process):
    """Detect looping by checking the current playback time."""
    last_position = None

    while True:
        try:
            # Get current playback position
            position_command = ["ffmpeg", "-i", "-", "-vn", "-af", "ashowinfo", "-f", "null", "-"]
            result = subprocess.run(position_command, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                output = result.stderr
                position_lines = [line for line in output.split("\n") if "pts_time:" in line]
                if position_lines:
                    latest_position = float(position_lines[-1].split("pts_time:")[-1].strip())

                    if last_position is not None and latest_position < last_position:
                        print("⚠️ Looping detected! Refreshing stream...")
                        return True

                    last_position = latest_position

            time.sleep(5)  # Check every 5 seconds

        except Exception as e:
            print(f"Error detecting looping: {e}")
            return False

def generate_stream(station_name):
    """Continuously stream audio and refresh when looping is detected."""
    last_audio_url = None

    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        if not stream_url:
            print(f"Fetching new stream for {station_name}...")
            latest_video = get_playlist_videos(YOUTUBE_PLAYLISTS[station_name])
            if latest_video:
                stream_url = extract_audio_url(latest_video)
                if stream_url:
                    with cache_lock:
                        stream_cache[station_name] = stream_url

        if not stream_url:
            print(f"No valid stream URL for {station_name}, retrying in 10s...")
            time.sleep(10)
            continue

        print(f"Streaming from: {stream_url}")

        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-http_persistent", "0",  
                "-i", stream_url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        if detect_looping(process):  # If looping detected, restart stream
            process.kill()
            continue

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

threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)