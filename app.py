from fastapi import FastAPI, Response
import yt_dlp
import time

app = FastAPI()

COOKIES_PATH = "/mnt/data/cookies.txt"

def get_playlist_audio_urls(playlist_url):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,  # Get only metadata (no downloads)
        "cookiefile": COOKIES_PATH,  # Use stored cookies
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",  # Change User-Agent
        "sleep_interval": 2,  # Add delay between requests
        "max_sleep_interval": 5,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(playlist_url, download=False)
            if result and "entries" in result:
                urls = []
                for entry in result["entries"]:
                    if "url" in entry:
                        urls.append(entry["url"])
                        time.sleep(2)  # Prevent rate-limiting
                return urls
        except Exception as e:
            print(f"Error fetching playlist: {e}")
    return []

def get_audio_stream(video_url):
    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "cookiefile": COOKIES_PATH,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info["url"]
        except Exception as e:
            print(f"Error fetching audio URL: {e}")
            return None

@app.get("/playlist.m3u")
def generate_m3u(playlist_url: str):
    video_urls = get_playlist_audio_urls(playlist_url)
    if not video_urls:
        return {"error": "No videos found or YouTube is blocking requests"}

    audio_urls = [get_audio_stream(video) for video in video_urls if video]
    audio_urls = [url for url in audio_urls if url]  # Remove failed fetches

    if not audio_urls:
        return {"error": "Failed to get audio streams"}

    m3u_content = "#EXTM3U\n" + "\n".join(f"#EXTINF:-1,Audio {i+1}\n{url}" for i, url in enumerate(audio_urls))

    return Response(content=m3u_content, media_type="audio/x-mpegurl")