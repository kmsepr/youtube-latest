from flask import Flask, Response
import subprocess
import time
import random

app = Flask(__name__)

STREAMS = {
    "zaytuna_new": [
        "https://www.youtube.com/live/NHO6loh7WAQ?si=Enbui2ahdkp0U7Xl"
        
    ],

    "qsc_old": [
        ##2005
        "https://youtu.be/1sVD5J4CiW0?si=1NKYE_e8e8zjf5Ct",
        "https://youtu.be/XYVCFhRSYjE?si=PSrd62Md24m2G1U9",
        "https://youtu.be/BjZpBjN4DMw?si=fIVesuH89l-wGpVM",
        "https://youtu.be/DLL6cqkD-WA?si=qIqCpExvshN7-41r",
        "https://youtu.be/_BGnQTHN2Jc?si=y7US_s7m2Jyl1nG9"
    ],
    
    "modern_history": [
        "https://www.youtube.com/live/ASnGYrBanlA?si=PURGYIDX1AqOej7q"
        
    ]
}

def get_audio_url(youtube_url):
    """Fetch fresh audio URL from YouTube."""
    yt_process = subprocess.run(
        ["yt-dlp", "--cookies", "/mnt/data/cookies.txt", "-f", "bestaudio", "-g", youtube_url],
        capture_output=True, text=True
    )
    return yt_process.stdout.strip()

def generate_audio(channel):
    """Continuously fetch fresh audio URLs and stream with FFmpeg."""
    while True:
        youtube_url = random.choice(STREAMS[channel])  # Pick a random stream
        audio_url = get_audio_url(youtube_url)
        
        if not audio_url:
            yield b"Error: Unable to fetch audio stream\n"
            time.sleep(5)  # Wait and retry
            continue

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", audio_url, "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1", "-f", "mp3", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=4096
        )

        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                yield chunk
        except Exception:
            process.kill()
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
