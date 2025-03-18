from flask import Flask, Response, jsonify
import subprocess
import os
import threading
import random
import time

app = Flask(__name__)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"
COOKIES_FILE = "/mnt/data/cookies.txt"
cache_lock = threading.Lock()
video_urls = []
current_index = 0

def fetch_playlist_videos():
    """Fetch all video URLs from the playlist and shuffle them."""
    global video_urls
    try:
        command = ["yt-dlp", "--flat-playlist", "-i", "--print", "%(url)s", YOUTUBE_PLAYLIST]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        new_video_urls = result.stdout.strip().split("\n")

        if new_video_urls:
            random.shuffle(new_video_urls)  # Shuffle the list
            with cache_lock:
                video_urls = new_video_urls
                print(f"✅ Fetched & shuffled {len(video_urls)} videos.")
        else:
            print("⚠️ No videos found in the playlist.")

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error fetching playlist videos: {e}")

def get_audio_url(video_url):
    """Fetch direct audio URL for the given video."""
    try:
        command = [
            "yt-dlp",
            "--cookies", COOKIES_FILE,
            "-f", "140",  # Ensuring M4A format
            "-g", video_url
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error getting audio URL: {e}")
        return None

def generate_audio():
    """Continuously stream audio, looping through the shuffled playlist."""
    global current_index

    while True:
        with cache_lock:
            if not video_urls:
                print("⚠️ Playlist is empty, refetching...")
                fetch_playlist_videos()

            video_url = video_urls[current_index]
            current_index = (current_index + 1) % len(video_urls)  # Move to next video (loop)

        print(f"🎵 Now Playing: {video_url}")

        audio_url = get_audio_url(video_url)
        if not audio_url:
            print("⚠️ Skipping to next video...")
            time.sleep(5)
            continue  # Skip if no audio found

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", audio_url, "-c", "copy", "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                yield chunk
        except GeneratorExit:
            process.terminate()
            break
        except Exception as e:
            print(f"⚠️ Error during streaming: {e}")

        process.terminate()

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/refresh')
def refresh():
    fetch_playlist_videos()
    return jsonify({"message": "Playlist refreshed & shuffled", "video_count": len(video_urls)})

if __name__ == '__main__':
    fetch_playlist_videos()  # Fetch videos at startup
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=True)