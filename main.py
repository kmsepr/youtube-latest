import subprocess
import os
from fastapi import FastAPI

app = FastAPI()

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLQ02IYL5pmhGFHxHEriqVmBn89cvSVMtz"
COOKIES_FILE = "/mnt/data/cookies.txt"

@app.get("/stream")
def stream_audio():
    try:
        process = subprocess.Popen(
            [
                "bash", "-c",
                f"yt-dlp --cookies {COOKIES_FILE} -f bestaudio -g '{YOUTUBE_PLAYLIST}' | while read -r url; do ffmpeg -re -i $url -acodec libmp3lame -b:a 128k -f mp3 icecast://source:password@your-server:8000/stream.mp3; done"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return {"status": "Streaming started with cookies!"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
