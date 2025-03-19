from fastapi import FastAPI, Response, Query
import yt_dlp
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COOKIES_PATH = "/mnt/data/cookies.txt"

# yt-dlp options
YDL_OPTS = {
    "quiet": True,
    "cookiefile": COOKIES_PATH,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "sleep_interval": 1,
    "max_sleep_interval": 3,
    "noplaylist": False,  # Allow playlists
}

def get_playlist_video_urls(playlist_url):
    """Fetch video URLs from a playlist."""
    options = {**YDL_OPTS, "extract_flat": True}
    urls = []
    
    with yt_dlp.YoutubeDL(options) as ydl:
        try:
            result = ydl.extract_info(playlist_url, download=False)
            if result and "entries" in result:
                urls = [entry["url"] for entry in result["entries"] if "url" in entry]
        except Exception as e:
            logger.error(f"Error fetching playlist: {e}")
    
    return urls

def get_audio_stream(video_url):
    """Fetch the direct audio stream URL for a given video."""
    options = {**YDL_OPTS, "format": "bestaudio"}
    
    with yt_dlp.YoutubeDL(options) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info.get("url")
        except Exception as e:
            logger.error(f"Error fetching audio URL for {video_url}: {e}")
            return None

@app.get("/playlist.m3u")
def generate_m3u(playlist_url: str = Query(..., title="YouTube Playlist URL")):
    """Generate an M3U playlist with direct audio stream URLs."""
    video_urls = get_playlist_video_urls(playlist_url)
    if not video_urls:
        return {"error": "No valid videos found or YouTube is blocking requests."}
    
    audio_urls = [get_audio_stream(url) for url in video_urls]
    audio_urls = [url for url in audio_urls if url]  # Filter out failed fetches
    
    if not audio_urls:
        return {"error": "Failed to retrieve any audio streams."}
    
    # Create M3U content
    m3u_content = "#EXTM3U\n" + "\n".join(
        f"#EXTINF:-1,Track {i+1}\n{url}" for i, url in enumerate(audio_urls)
    )
    
    return Response(content=m3u_content, media_type="audio/x-mpegurl")
