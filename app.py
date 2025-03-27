from flask import Flask, Response
import subprocess

app = Flask(__name__)

STREAMS = {
    "zaytuna_new": "https://www.youtube.com/live/NHO6loh7WAQ?si=Enbui2ahdkp0U7Xl",
    "modern_history": "https://www.youtube.com/live/ASnGYrBanlA?si=PURGYIDX1AqOej7q"
}

def generate_audio(youtube_url):
    # Extract direct audio URL using yt-dlp with cookies
    yt_process = subprocess.run(
    ["yt-dlp", "--cookies", "/mnt/data/cookies.txt", "-f", "bestaudio", "-g", youtube_url],
        capture_output=True, text=True
    )
    audio_url = yt_process.stdout.strip()

    if not audio_url:
        yield b"Error: Unable to fetch audio stream\n"
        return

    # Stream using ffmpeg
    process = subprocess.Popen(
    ["ffmpeg", "-re", "-i", audio_url, "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1", "-f", "mp3", "pipe:1"],
    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=4096
)

    try:
        for chunk in iter(lambda: process.stdout.read(4096), b""):
            yield chunk
    finally:
        process.kill()

@app.route("/stream/<channel>")
def stream(channel):
    if channel not in STREAMS:
        return "Channel not found", 404

    return Response(generate_audio(STREAMS[channel]), content_type="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)