from flask import Flask, Response, jsonify
import subprocess
import os

app = Flask(__name__)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"

def generate_audio():
    """Fetches YouTube playlist audio and streams it as MP3 (40 kbps)."""
    command_yt = [
        "yt-dlp", "-f", "249", "-o", "-", YOUTUBE_PLAYLIST
    ]

    process_yt = subprocess.Popen(command_yt, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    command_ffmpeg = [
        "ffmpeg", "-i", "-", "-vn", "-acodec", "libmp3lame", "-b:a", "40k", "-ac", "1", "-f", "mp3", "-"
    ]

    process_ffmpeg = subprocess.Popen(command_ffmpeg, stdin=process_yt.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        for chunk in iter(lambda: process_ffmpeg.stdout.read(1024), b""):
            yield chunk
    except GeneratorExit:
        process_ffmpeg.terminate()
        process_yt.terminate()
    except Exception as e:
        print(f"⚠️ Error: {e}")

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the radio stream"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Koyeb requires port 8080
    app.run(host='0.0.0.0', port=port, threaded=True)