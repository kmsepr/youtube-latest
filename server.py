import subprocess
import time
import threading
from flask import Flask, Response

app = Flask(__name__)

# 📡 List of YouTube Channels
YOUTUBE_STREAMS = {
    "media_one": "https://www.youtube.com/@MediaoneTVLive",
    "shajahan_rahmani": "https://www.youtube.com/@ShajahanRahmaniOfficial",
    "qsc_mukkam": "https://www.youtube.com/c/quranstudycentremukkam",
    "valiyudheen_faizy": "https://www.youtube.com/@voiceofvaliyudheenfaizy600",
    "skicr_tv": "https://www.youtube.com/@SKICRTV",
    "yaqeen_institute": "https://www.youtube.com/@yaqeeninstituteofficial",
    "bayyinah_tv": "https://www.youtube.com/@bayyinah",
    "eft_guru": "https://www.youtube.com/@EFTGuru-ql8dk",
    "unacademy_ias": "https://www.youtube.com/@UnacademyIASEnglish",
    "studyiq_hindi": "https://www.youtube.com/@StudyIQEducationLtd",
    "aljazeera_arabic": "https://www.youtube.com/@aljazeera",
    "aljazeera_english": "https://www.youtube.com/@AlJazeeraEnglish",
    "entri_degree": "https://www.youtube.com/@EntriDegreeLevelExams",
    "xylem_psc": "https://www.youtube.com/@XylemPSC",
    "sleepy_classes": "https://www.youtube.com/@sleepyclassesias",
    "entri_app": "https://www.youtube.com/@entriapp",
    "entri_ias": "https://www.youtube.com/@EntriIAS",
    "studyiq_english": "https://www.youtube.com/@studyiqiasenglish"
}

# 🌍 Store latest stream URLs
stream_cache = {}
cache_lock = threading.Lock()

def get_live_audio_url(youtube_url):
    """Fetch the latest direct audio URL from a YouTube Live Stream."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "--force-generic-extractor",
        "-f", "91",
        "-g", youtube_url + "/live"  # Append /live for live stream
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip() if result.stdout else None

        if audio_url:
            print(f"✅ LIVE Audio: {youtube_url}")
        else:
            print(f"❌ No live stream: {youtube_url}")

        return audio_url

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error fetching live audio URL for {youtube_url}: {e}")
        return None

def get_latest_video_url(channel_url):
    """Fetch the latest video URL from a YouTube channel."""
    command = [
        "yt-dlp",
        "--cookies", "/mnt/data/cookies.txt",
        "--force-generic-extractor",
        "--get-url",
        "-f", "18",  # 18 is 360p MP4 format
        "--match-filter", "is_live = False",
        channel_url
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        video_url = result.stdout.strip() if result.stdout else None

        if video_url:
            print(f"✅ Latest Video: {video_url}")
        else:
            print(f"❌ No videos found for {channel_url}")

        return video_url

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error fetching latest video URL for {channel_url}: {e}")
        return None

def refresh_stream_urls():
    """Refresh YouTube stream URLs every 30 minutes."""
    while True:
        with cache_lock:
            for station, url in YOUTUBE_STREAMS.items():
                live_url = get_live_audio_url(url)
                if live_url:
                    stream_cache[station + "_live"] = live_url  # Store with "_live"

                video_url = get_latest_video_url(url)
                if video_url:
                    stream_cache[station + "_video"] = video_url  # Store with "_video"
        time.sleep(1800)  # Refresh every 30 minutes

def generate_audio_stream(station_name):
    """Streams live audio using FFmpeg."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name + "_live")

        if not stream_url:
            print(f"⚠️ No valid stream URL for {station_name}, fetching a new one...")
            with cache_lock:
                youtube_url = YOUTUBE_STREAMS.get(station_name)
                if youtube_url:
                    stream_url = get_live_audio_url(youtube_url)
                    if stream_url:
                        stream_cache[station_name + "_live"] = stream_url

        if not stream_url:
            print(f"❌ Failed to fetch stream URL for {station_name}, retrying in 30s...")
            time.sleep(30)
            continue

        print(f"🎵 Streaming from: {stream_url}")

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", stream_url,
             "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1",
             "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")

        print("🔄 FFmpeg stopped, retrying in 5s...")
        process.kill()
        time.sleep(5)

def generate_video_stream(station_name):
    """Streams the latest video using FFmpeg."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name + "_video")

        if not stream_url:
            print(f"⚠️ No valid video URL for {station_name}, fetching a new one...")
            with cache_lock:
                youtube_url = YOUTUBE_STREAMS.get(station_name)
                if youtube_url:
                    stream_url = get_latest_video_url(youtube_url)
                    if stream_url:
                        stream_cache[station_name + "_video"] = stream_url

        if not stream_url:
            print(f"❌ Failed to fetch video URL for {station_name}, retrying in 30s...")
            time.sleep(30)
            continue

        print(f"📺 Streaming from: {stream_url}")

        process = subprocess.Popen(
            ["ffmpeg", "-re", "-i", stream_url,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
             "-f", "mp4", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")

        print("🔄 FFmpeg stopped, retrying in 5s...")
        process.kill()
        time.sleep(5)

@app.route("/play/<station_name>")
def play_audio(station_name):
    """Stream YouTube Live Audio."""
    if station_name not in YOUTUBE_STREAMS:
        return "⚠️ Station not found", 404

    return Response(generate_audio_stream(station_name), mimetype="audio/mpeg")

@app.route("/latest/<station_name>")
def latest_video(station_name):
    """Stream the latest YouTube video."""
    if station_name not in YOUTUBE_STREAMS:
        return "⚠️ Station not found", 404

    return Response(generate_video_stream(station_name), mimetype="video/mp4")

# 🚀 Start URL refresher thread
threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
