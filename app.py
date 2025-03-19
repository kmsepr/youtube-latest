from fastapi import FastAPI, Response
import yt_dlp

app = FastAPI()

def get_playlist_audio_urls(playlist_url):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,  # Get only metadata (no downloads)
        "force_generic_extractor": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)
        if "entries" in result:
            return [entry["url"] for entry in result["entries"]]
    return []

def get_audio_stream(video_url):
    ydl_opts = {"format": "bestaudio", "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info["url"]

@app.get("/playlist.m3u")
def generate_m3u(playlist_url: str):
    video_urls = get_playlist_audio_urls(playlist_url)
    if not video_urls:
        return {"error": "No videos found"}
    
    audio_urls = [get_audio_stream(video) for video in video_urls]
    
    m3u_content = "#EXTM3U\n" + "\n".join(f"#EXTINF:-1,Audio {i+1}\n{url}" for i, url in enumerate(audio_urls))
    
    return Response(content=m3u_content, media_type="audio/x-mpegurl")