import subprocess
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

# 📡 List of YouTube Live Streams
YOUTUBE_STREAMS = {
    "media_one": "https://www.youtube.com/@MediaoneTVLive/live",
    "shajahan_rahmani": "https://www.youtube.com/@ShajahanRahmaniOfficial/live",
    "aljazeera_arabic": "https://www.youtube.com/@aljazeera/live",
    "aljazeera_english": "https://www.youtube.com/@AlJazeeraEnglish/live"
}

# 🎵 List of YouTube Playlists
PLAYLISTS = {
    "yaqeen_latest": "https://youtube.com/playlist?list=PLQ02IYL5pmhEw1lGauK0-NKXqcCDlWtq7",
    "zaytuna_latest": "https://youtube.com/playlist?list=PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck"
}

# 🌍 Cached YouTube stream URLs to avoid frequent re-fetching
stream_cache = {}
cache_lock = threading.Lock()

def get_audio_url(youtube_url):
    """Fetch the latest direct audio URL from YouTube."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "--force-generic-extractor",
        "-f", "91/bestaudio",  # Try format 91 first, fallback to bestaudio
        "-g", youtube_url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_urls = result.stdout.strip().split("\n")

        if audio_urls:
            print(f"✅ Fetched URL: {audio_urls[0]}")
            return audio_urls[0]
        else:
            print(f"❌ No playable audio found for {youtube_url}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error fetching audio URL: {e}")
        return None

def refresh_stream_urls():
    """Refresh YouTube stream URLs every 15 minutes to avoid expiration."""
    while True:
        with cache_lock:
            for station, url in YOUTUBE_STREAMS.items():
                new_url = get_audio_url(url)
                if new_url:
                    stream_cache[station] = new_url
        time.sleep(900)  # Refresh every 15 minutes

def generate_stream(station_name):
    """Streams audio from a YouTube Live stream."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        if not stream_url:
            print(f"⚠️ No valid stream URL for {station_name}, fetching a new one...")
            with cache_lock:
                youtube_url = YOUTUBE_STREAMS.get(station_name)
                if youtube_url:
                    stream_url = get_audio_url(youtube_url)
                    if stream_url:
                        stream_cache[station_name] = stream_url

        if not stream_url:
            print(f"❌ Failed to fetch stream URL for {station_name}, retrying in 10s...")
            time.sleep(10)
            continue

        print(f"🎵 Streaming from: {stream_url}")

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", stream_url,
             "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1",
             "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            print(f"🛑 Stopping stream: {station_name}")
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")

        print("🔄 FFmpeg stopped, retrying in 5s...")
        process.kill()
        time.sleep(5)

def generate_playlist_stream(playlist_url):
    """Streams audio from a YouTube playlist, switching to the next track automatically."""
    while True:
        audio_url = get_audio_url(playlist_url)

        if not audio_url:
            print("⚠️ No valid stream URL, retrying in 30 seconds...")
            time.sleep(30)
            continue

        print(f"🎵 Streaming from: {audio_url}")

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", audio_url,
             "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1",
             "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            print("🛑 Stopping playlist stream.")
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")

        print("🔄 FFmpeg stopped, retrying with next track...")
        process.kill()
        time.sleep(5)

@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in YOUTUBE_STREAMS:
        return "⚠️ Station not found", 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

@app.route("/play_playlist/<playlist_id>")
def play_playlist(playlist_id):
    playlist_url = PLAYLISTS.get(playlist_id)

    if not playlist_url:
        return "⚠️ Playlist not found", 404

    return Response(generate_playlist_stream(playlist_url), mimetype="audio/mpeg")

# 🚀 Start the URL refresher thread
threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)