from flask import Flask, Response, jsonify
import subprocess
import os

app = Flask(__name__)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"

def generate_audio():
    command = [
        "yt-dlp", "-f", "bestaudio", "-o", "-", YOUTUBE_PLAYLIST
    ]

    process_yt = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    process_ffmpeg = subprocess.Popen(
        ["ffmpeg", "-i", "-", "-acodec", "libmp3lame", "-b:a", "128k", "-f", "mp3", "-"],
        stdin=process_yt.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

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
    port = int(os.environ.get("PORT", 8080))  # Koyeb uses port 8080
    app.run(host='0.0.0.0', port=port, threaded=True)