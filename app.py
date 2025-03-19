from fastapi import FastAPI, Query
import yt_dlp
import time

app = FastAPI()

def fetch_playlist(playlist_url, max_retries=99999, retry_delay=10):
    """Fetches YouTube playlist and retries indefinitely on failure."""
    retries = 0
    while retries < max_retries:
        try:
            ydl_opts = {
                'quiet': True,
                'extractor_args': {'youtubetab': 'skip=authcheck'},
                'cookiefile': '/mnt/data/cookies.txt',  # Ensure this file is in Netscape format!
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(playlist_url, download=False)
                if result and 'entries' in result:
                    print("✅ Playlist fetched successfully!")
                    return result['entries']
        except yt_dlp.utils.DownloadError as e:
            print(f"⚠️ Error fetching playlist: {e}")
        
        retries += 1
        print(f"🔄 Retrying... ({retries}/{max_retries}) in {retry_delay} seconds...")
        time.sleep(retry_delay)

    print("❌ Max retries reached. Giving up.")
    return None

@app.get("/playlist.m3u")
async def get_playlist(playlist_url: str = Query(..., description="YouTube Playlist URL")):
    """Endpoint to fetch and return M3U playlist."""
    print(f"🎵 Fetching playlist: {playlist_url}")
    playlist_entries = fetch_playlist(playlist_url)

    if not playlist_entries:
        return {"error": "Failed to fetch playlist after multiple retries."}

    m3u_content = "#EXTM3U\n"
    for entry in playlist_entries:
        title = entry.get("title", "Unknown")
        url = entry.get("url", "")
        m3u_content += f"#EXTINF:-1,{title}\n{url}\n"

    return m3u_content
