from flask import Flask, Response, request, jsonify
import subprocess

app = Flask(__name__)

# Path to cookies file
COOKIES_PATH = "/mnt/data/cookies.txt"

# Dictionary of YouTube playlists
PLAYLISTS = {
    "playlist1": "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN",
    "playlist2": "https://youtube.com/playlist?list=PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
}

def generate_audio(playlist_url):
    command = [
        "yt-dlp",
        "--cookies", COOKIES_PATH,
        "--force-generic-extractor",
        "-f", "91",  # Using format 91
        "-o", "-",
        playlist_url
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ffmpeg_command = [
        "ffmpeg",
        "-i", "pipe:0",
        "-acodec", "libmp3lame",
        "-b:a", "64k",
        "-f", "mp3",
        "pipe:1"
    ]
    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        while True:
            chunk = ffmpeg_process.stdout.read(1024)
            if not chunk:
                break
            yield chunk
    except GeneratorExit:
        process.terminate()
        ffmpeg_process.terminate()

@app.route('/stream')
def stream():
    playlist_key = request.args.get("playlist", "playlist1")  # Default to "playlist1"
    playlist_url = PLAYLISTS.get(playlist_key)

    if not playlist_url:
        return jsonify({"error": "Invalid playlist key. Choose from: " + ", ".join(PLAYLISTS.keys())}), 400

    return Response(generate_audio(playlist_url), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({
        "message": "Go to /stream?playlist=playlist1 (or playlist2) to listen to a specific playlist",
        "available_playlists": list(PLAYLISTS.keys())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
