import os
import subprocess
import time
import threading
from flask import Flask, Response, jsonify

app = Flask(__name__)

# Mapping of station names to YouTube channel IDs
YOUTUBE_CHANNELS = {
    "entri_app": "UC9VKXPGzRIs9raMlCwzljtA",
    "media_one": "UC-f7r46JhYv78q5pGrO6ivA",  # Media One channel
}

# Cache to store the latest audio stream URLs
stream_cache = {}
cache_lock = threading.Lock()


def get_latest_video_url(channel_id):
    """Fetch the latest video URL using yt-dlp subprocess."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "--force-generic-extractor",
        "--extract-flat", "true",  # Get only metadata without downloading
        "--playlist-end", "1",  # Fetch only the latest video
        "-g", f"https://www.youtube.com/channel/{channel_id}"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        video_url = result.stdout.strip()
        if video_url:
            return video_url
    except subprocess.CalledProcessError as e:
        print(f"Error fetching latest video: {e.stderr}")

    return None


def get_audio_url(youtube_url):
    """Extract the direct audio URL from a YouTube video using yt-dlp subprocess."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "--force-generic-extractor",
        "-f", "bestaudio",
        "-g", youtube_url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        if audio_url:
            return audio_url
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio URL: {e.stderr}")

    return None


def refresh_stream_url():
    """Refresh the audio stream URLs periodically."""
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
    """Stream audio using FFmpeg, updating the URL when it expires."""
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
             "-vn", "-acodec", "libmp3lame", "-b:a", "128k", "-ac", "2",
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