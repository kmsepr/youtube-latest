from fastapi import FastAPI, Response
import yt_dlp

app = FastAPI()

# Path to uploaded cookies
COOKIES_PATH = "/mnt/data/cookies.txt"

def get_playlist_audio_urls(playlist_url):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,  # Get only metadata (no downloads)
        "cookiefile": COOKIES_PATH,  # Use cookies for authentication
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)
        if result and "entries" in result:
            return [entry["url"] for entry in result["entries"] if "url" in entry]
    return []

def get_audio_stream(video_url):
    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "cookiefile": COOKIES_PATH,  # Use cookies for better access
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info.get("url")
        except Exception as e:
            print(f"Error fetching stream URL for {video_url}: {e}")
            return None

@app.get("/playlist.m3u")
def generate_m3u(playlist_url: str):
    video_urls = get_playlist_audio_urls(playlist_url)
    if not video_urls:
        return {"error": "No videos found"}

    audio_urls = [get_audio_stream(video) for video in video_urls]
    audio_urls = [url for url in audio_urls if url]  # Remove failed URLs

    if not audio_urls:
        return {"error": "No playable audio found"}

    # Generate M3U playlist
    m3u_content = "#EXTM3U\n" + "\n".join(f"#EXTINF:-1,Audio {i+1}\n{url}" for i, url in enumerate(audio_urls))

    return Response(content=m3u_content, media_type="audio/x-mpegurl")