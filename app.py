import os
import subprocess
import time
import threading
from flask import Flask, Response, jsonify
import requests
import yt_dlp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)

# Mapping of station names to YouTube channel IDs
YOUTUBE_CHANNELS = {
    "entri_app": "UC9VKXPGzRIs9raMlCwzljtA",
    "media_one": "UC-f7r46JhYv78q5pGrO6ivA",
}

# Cache to store the latest audio stream URLs
stream_cache = {}
cache_lock = threading.Lock()

def get_latest_video_url(channel_id):
    """Fetch the latest video URL from a YouTube channel using the YouTube Data API."""
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "channelId": channel_id,
        "order": "date",
        "part": "id",
        "maxResults": 1,
        "type": "video"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            print(f"No videos found for channel ID: {channel_id}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching latest video: {e}")
        return None

def get_audio_url(youtube_url):
    """Extract the direct audio URL from a YouTube video using yt-dlp."""
    ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'cookies': '/mnt/data/cookies.txt'  # Ensure the correct path
}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            formats = info_dict.get('formats', [])
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    return f.get('url')
        print(f"No audio formats found for {youtube_url}")
        return None
    except yt_dlp.utils.DownloadError as e:
        print(f"Error extracting audio URL: {e}")
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
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"Stream error: {e}")

        print("FFmpeg stopped, retrying in 5s...")
        process.kill()
        time.sleep(5)

@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in YOUTUBE_CHANNELS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

# Start the URL refresher thread
threading.Thread(target=refresh_stream_url, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)