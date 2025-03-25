import os
import subprocess
import time
import threading
import random
import logging
from flask import Flask, Response, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 📌 YouTube Video Links for Different Stations
STATIONS = {
    "modern_history": [
        "https://www.youtube.com/watch?v=PrUn1sf3WFk",
        "https://www.youtube.com/watch?v=3Da14COqSwk",
        "https://www.youtube.com/watch?v=RE5Em_Hg7dA",
        "https://www.youtube.com/watch?v=4nl1Z6xUOyY",
        "https://www.youtube.com/watch?v=rUUl5RUnQcw",
        "https://www.youtube.com/watch?v=_RnQCC6Df6Q",
        "https://www.youtube.com/watch?v=CAYIYngTRPE",
    ]
}

stream_cache = {}
cache_lock = threading.Lock()
CACHE_REFRESH_INTERVAL = 1500  # Refresh every 25 minutes


def extract_audio_url(video_url):
    """Extract direct audio URL using yt-dlp with format 91."""
    command = [
        "yt-dlp", "--cookies", "/mnt/data/cookies.txt",
        "-f", "91", "-g", video_url
    ]
    
    logging.info(f"Extracting audio from: {video_url}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        
        if audio_url:
            logging.info(f"Extracted URL: {audio_url}")
            return audio_url
        else:
            logging.warning("Warning: No URL extracted!")
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to extract audio: {e}")
        logging.error(f"yt-dlp stderr: {e.stderr}")
    
    return None


def refresh_stream_urls():
    """Periodically update stream URLs."""
    while True:
        with cache_lock:
            for station, video_list in STATIONS.items():
                video_url = random.choice(video_list)
                audio_url = extract_audio_url(video_url)

                if audio_url:
                    stream_cache[station] = audio_url
                    logging.info(f"Updated cache for {station}: {audio_url}")
                else:
                    logging.warning(f"Failed to refresh stream for {station}")
        
        time.sleep(CACHE_REFRESH_INTERVAL)


def generate_stream(station_name):
    """Continuously stream audio with automatic refresh."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        if not stream_url:
            logging.info(f"Fetching new stream for {station_name}...")
            video_url = random.choice(STATIONS[station_name])
            stream_url = extract_audio_url(video_url)

            if stream_url:
                with cache_lock:
                    stream_cache[station_name] = stream_url

        if not stream_url:
            logging.warning(f"No valid stream URL for {station_name}, retrying in 10s...")
            time.sleep(10)
            continue

        logging.info(f"Streaming from: {stream_url}")

        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "5", "-fflags", "nobuffer", "-flags", "low_delay",
                "-http_persistent", "0",  
                "-i", stream_url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "512k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except (GeneratorExit, Exception):
            logging.error(f"Stream error for {station_name}, restarting stream...")
            process.kill()
            time.sleep(5)
            continue


@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in STATIONS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")


# Start the background thread for refreshing URLs
threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
