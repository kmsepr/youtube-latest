import time
import subprocess
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI()

COOKIES_FILE = "/mnt/data/cookies.txt"
FFMPEG_CMD = [
    "ffmpeg", "-re", "-i", "-", "-acodec", "libmp3lame", "-b:a", "128k",
    "-f", "mp3", "pipe:1"
]

def get_audio_url(playlist_url):
    """ Extracts the first playable audio URL from the YouTube playlist. """
    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": False,
        "quiet": True,
        "extract_flat": False,
        "cookies": COOKIES_FILE,
    }

    while True:  # Keep retrying if it fails
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if "entries" in info and info["entries"]:
                    for entry in info["entries"]:
                        if entry and "url" in entry:
                            return entry["url"]
        except Exception as e:
            print(f"Error fetching audio URL: {e}. Retrying in 5 seconds...")
            time.sleep(5)

@app.get("/stream")
def stream_audio(playlist_url: str):
    """ Streams YouTube audio using ffmpeg. """
    audio_url = get_audio_url(playlist_url)
    if not audio_url:
        raise HTTPException(status_code=500, detail="Failed to fetch audio URL.")

    def generate():
        process = subprocess.Popen(
            ["ffmpeg", "-i", audio_url, "-acodec", "libmp3lame", "-b:a", "128k", "-f", "mp3", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        try:
            while True:
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                yield chunk
        except GeneratorExit:
            process.kill()

    return StreamingResponse(generate(), media_type="audio/mpeg")
