from fastapi import FastAPI
import yt_dlp

app = FastAPI()

def get_latest_video_url(channel_url):
    ydl_opts = {"quiet": True, "extract_flat": True, "force_generic_extractor": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)
        if "entries" in result:
            latest_video = result["entries"][0]  # Get latest video
            return latest_video["url"]
    return None

def get_audio_stream(video_url):
    ydl_opts = {"format": "bestaudio", "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info["url"]

@app.get("/stream")
def stream_audio(channel_url: str):
    video_url = get_latest_video_url(channel_url)
    if not video_url:
        return {"error": "No videos found"}
    audio_url = get_audio_stream(video_url)
    return {"audio_url": audio_url}