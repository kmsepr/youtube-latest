from flask import Flask, Response
import subprocess
import time
import random
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

STREAMS = {
    "zaytuna_new": [
        "https://www.youtube.com/live/NHO6loh7WAQ?si=Enbui2ahdkp0U7Xl"
    ],
    "qsc_old": [
        "https://youtu.be/1sVD5J4CiW0?si=1NKYE_e8e8zjf5Ct",
        "https://youtu.be/XYVCFhRSYjE?si=PSrd62Md24m2G1U9",
        "https://youtu.be/BjZpBjN4DMw?si=fIVesuH89l-wGpVM",
        "https://youtu.be/DLL6cqkD-WA?si=qIqCpExvshN7-41r",
        "https://youtu.be/_BGnQTHN2Jc?si=y7US_s7m2Jyl1nG9",
        "https://youtu.be/1Obw6v4pihE?si=RuY_3q4qoYpFRVW8",
        "https://youtu.be/pdNLMvsFOQo?si=QhQFCO2Iahb4lf1l",
        "https://youtu.be/HHxySeLVvpU?si=9qmgw3ds-vL_prXB"
    ],
    "modern_history": [
        "https://www.youtube.com/live/ASnGYrBanlA?si=PURGYIDX1AqOej7q"
    ]
}

def get_audio_url(youtube_url):
    """Fetch fresh audio URL from YouTube using yt-dlp."""
    try:
        yt_process = subprocess.run(
            ["yt-dlp", "--cookies", "/mnt/data/cookies.txt", "-f", "bestaudio", "-g", youtube_url],
            capture_output=True, text=True
        )
        if yt_process.returncode != 0:
            logging.error(f"yt-dlp failed: {yt_process.stderr}")
            return None
        return yt_process.stdout.strip()
    except Exception as e:
        logging.error(f"Error fetching audio URL: {e}")
        return None

def generate_audio(channel):
    """Continuously fetch fresh audio URLs and stream with FFmpeg."""
    while True:
        youtube_url = random.choice(STREAMS[channel])  # Pick a random stream
        audio_url = get_audio_url(youtube_url)

        if not audio_url:
            logging.warning(f"Failed to fetch audio for {channel}, retrying...")
            yield b"Error: Unable to fetch audio stream\n"
            time.sleep(5)  # Wait and retry
            continue

        logging.info(f"Streaming from {audio_url}")

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", audio_url, "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1", "-f", "mp3", "-bufsize", "64k", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                yield chunk
        except Exception as e:
            logging.error(f"FFmpeg error: {e}")
        finally:
            process.kill()
            time.sleep(2)  # Small delay before retrying with a fresh link

@app.route("/stream/<channel>")
def stream(channel):
    if channel not in STREAMS:
        return "Channel not found", 404

    return Response(generate_audio(channel), content_type="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)