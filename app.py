from flask import Flask, Response, jsonify
import subprocess

app = Flask(__name__)

# Define unique paths for each playlist
PLAYLISTS = {
    "playlist1": "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN",
    "playlist2": "https://youtube.com/playlist?list=PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
}

COOKIES_PATH = "/mnt/data/cookies.txt"

def generate_audio(playlist_url):
    command = [
        "yt-dlp",
        "--cookies", COOKIES_PATH,
        "--force-generic-extractor",
        "-f", "bestaudio",
        "-o", "-",
        playlist_url
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    ffmpeg_command = [
        "ffmpeg",
        "-i", "pipe:0",
        "-acodec", "libmp3lame",
        "-b:a", "64k",  # Set bitrate to 64kbps
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

# Dynamic URL for each playlist
@app.route('/stream/<playlist_name>')
def stream(playlist_name):
    playlist_url = PLAYLISTS.get(playlist_name)
    
    if not playlist_url:
        return jsonify({"error": "Invalid playlist name"}), 404

    return Response(generate_audio(playlist_url), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({
        "message": "Use the following unique links to stream playlists:",
        "stream_links": {name: f"/stream/{name}" for name in PLAYLISTS.keys()}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
