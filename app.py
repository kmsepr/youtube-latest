from flask import Flask, Response, jsonify
import subprocess

app = Flask(__name__)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"
COOKIES_PATH = "/mnt/data/cookies.txt"  # Ensure your cookies.txt file is uploaded here

def generate_audio():
    yt_dlp_cmd = [
        "yt-dlp",
        "--cookies", COOKIES_PATH,
        "--force-generic-extractor",
        "-f", "bestaudio",
        "-o", "-",
        YOUTUBE_PLAYLIST
    ]
    
    process_yt = subprocess.Popen(yt_dlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", "pipe:0",
        "-acodec", "libmp3lame",
        "-b:a", "64k",  # 64 kbps bitrate
        "-f", "mp3",
        "pipe:1"
    ]

    process_ffmpeg = subprocess.Popen(ffmpeg_cmd, stdin=process_yt.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    process_yt.stdout.close()  # Allow yt-dlp to close when FFmpeg stops

    while True:
        chunk = process_ffmpeg.stdout.read(1024)
        if not chunk:
            break
        yield chunk

    process_ffmpeg.terminate()
    process_yt.terminate()

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the radio stream"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
