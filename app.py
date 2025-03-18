from flask import Flask, Response, jsonify
import subprocess
import os
import random

app = Flask(__name__)

# Playlist URL
YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"

# Path to cookies file (replace with your actual path)
COOKIES_FILE = "/mnt/data/cookies.txt"

# List to store shuffled playlist
shuffled_videos = []
current_index = 0

# Extract and shuffle video URLs
def refresh_playlist():
    global shuffled_videos, current_index

    command = ["yt-dlp", "--flat-playlist", "-i", "--print", "%(url)s", YOUTUBE_PLAYLIST]
    result = subprocess.run(command, capture_output=True, text=True)

    video_urls = result.stdout.strip().split("\n")
    if video_urls:
        random.shuffle(video_urls)  # Shuffle the videos
        shuffled_videos = video_urls
        current_index = 0  # Reset index

# Get next video URL from the shuffled playlist
def get_next_video():
    global current_index

    if not shuffled_videos or current_index >= len(shuffled_videos):
        refresh_playlist()

    if shuffled_videos:
        video_url = shuffled_videos[current_index]
        current_index += 1
        return video_url
    return None

# Stream audio from a video
def generate_audio(video_url):
    command = [
        "yt-dlp", "--cookies", COOKIES_FILE, "-f", "bestaudio", "-o", "-", video_url
    ]

    process_yt = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    process_ffmpeg = subprocess.Popen(
        ["ffmpeg", "-i", "pipe:0", "-acodec", "libmp3lame", "-b:a", "40k", "-f", "mp3", "-"],
        stdin=process_yt.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

    try:
        for chunk in iter(lambda: process_ffmpeg.stdout.read(1024), b""):
            yield chunk
    except GeneratorExit:
        process_ffmpeg.terminate()
        process_yt.terminate()
    except Exception as e:
        print(f"⚠️ Error: {e}")

@app.route('/stream')
def stream():
    video_url = get_next_video()
    if not video_url:
        return Response("No videos found in the playlist", status=500)

    return Response(generate_audio(video_url), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the radio stream"})

if __name__ == '__main__':
    refresh_playlist()  # Load playlist on startup
    port = int(os.environ.get("PORT", 8080))  # Koyeb requires port 8080
    app.run(host='0.0.0.0', port=port, threaded=True)
