from flask import Flask, Response
import subprocess
import os

app = Flask(__name__)

# Replace with your actual YouTube Playlist URL
PLAYLIST_URL = "https://youtube.com/playlist?list=PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck&si=HLZUvAdhoUJnwDHN"

# Extract all video URLs from the playlist
def get_playlist():
    cmd = f'yt-dlp -j --flat-playlist "{PLAYLIST_URL}" | jq -r \'.url\''
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip().split("\n")

# Start FFmpeg streaming for a given YouTube URL
def stream_audio(url):
    cmd = f'yt-dlp -f bestaudio -g "{url}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    stream_url = result.stdout.strip()
    
    if stream_url:
        ffmpeg_cmd = [
            "ffmpeg", "-re", "-i", stream_url,
            "-acodec", "libmp3lame", "-b:a", "128k", "-f", "mp3", "pipe:1"
        ]
        return subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return None

@app.route("/stream")
def audio_stream():
    playlist = get_playlist()
    if not playlist:
        return "No videos found in the playlist.", 404

    def generate():
        for video_url in playlist:
            process = stream_audio(video_url)
            if process:
                while True:
                    chunk = process.stdout.read(1024)
                    if not chunk:
                        break
                    yield chunk
                process.terminate()

    return Response(generate(), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)