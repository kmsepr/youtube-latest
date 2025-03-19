from fastapi import FastAPI, Query
import yt_dlp
import time

app = FastAPI()

def fetch_audio_urls(playlist_url, max_retries=99999, retry_delay=10):
    """Fetch direct audio URLs from a YouTube playlist with retries."""
    retries = 0
    while retries < max_retries:
        try:
            ydl_opts = {
                'quiet': True,
                'format': 'bestaudio/best',
                'extract_flat': False,  # Fully extract details
                'cookiefile': '/mnt/data/cookies.txt',  # Use a cookie file if needed
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
    """Returns an M3U playlist for streaming in an internet radio."""
    print(f"🎵 Fetching YouTube playlist: {playlist_url}")
    playlist_entries = fetch_audio_urls(playlist_url)

    if not playlist_entries:
        return {"error": "Failed to fetch playlist after multiple retries."}

    m3u_content = "#EXTM3U\n"
    for entry in playlist_entries:
        title = entry.get("title", "Unknown")
        formats = entry.get("formats", [])
        best_audio_url = None
        
        # Get the best audio format
        for fmt in formats:
            if "audio" in fmt.get("format_note", "").lower():
                best_audio_url = fmt.get("url")
                break

        if best_audio_url:
            m3u_content += f"#EXTINF:-1,{title}\n{best_audio_url}\n"
        else:
            print(f"⚠️ No playable audio found for {title}")

    # Save the M3U file locally for Koyeb hosting
    with open("/mnt/data/playlist.m3u", "w") as f:
        f.write(m3u_content)

    return {"message": "M3U playlist created!", "url": "/mnt/data/playlist.m3u"}
