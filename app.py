from flask import Flask, Response, jsonify
import subprocess

app = Flask(__name__)

# Path to cookies file
COOKIES_PATH = "/mnt/data/cookies.txt"

# List of YouTube playlists
PLAYLISTS = {
    "playlist1": "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN",
    "playlist2": "https://youtube.com/playlist?list=PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
}

def generate_audio():
    for playlist_url in YOUTUBE_PLAYLISTS:
        command = [
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--force-generic-extractor",
            "-f", "91",  # Using format 91
            "-o", "-",
            playlist_url
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        ffmpeg_command = [
            "ffmpeg",
            "-i", "pipe:0",
            "-acodec", "libmp3lame",
            "-b:a", "64k",
            "-f", "mp3",
            "pipe:1"
        ]
        ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=process.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        while True:
            chunk = ffmpeg_process.stdout.read(1024)
            if not chunk:
                break
            yield chunk

        process.terminate()
        ffmpeg_process.terminate()

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the radio stream"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
