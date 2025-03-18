from flask import Flask, Response, jsonify, request
import subprocess

app = Flask(__name__)

PLAYLISTS = {
    "default": "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN",
    "playlist2": "https://www.youtube.com/playlist?list=ANOTHER_PLAYLIST_ID"
}

def generate_audio(playlist_url):
    command = f'yt-dlp -f "bestaudio" -o - "{playlist_url}" | ffmpeg -i - -acodec libmp3lame -b:a 96k -f mp3 -'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=4096, shell=True)
    
    try:
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            yield chunk
    except GeneratorExit:
        process.terminate()

@app.route('/stream')
def stream():
    playlist_name = request.args.get("playlist", "default")  # Get playlist from query param
    playlist_url = PLAYLISTS.get(playlist_name, PLAYLISTS["default"])  # Default if not found
    return Response(generate_audio(playlist_url), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream?playlist=default to listen to the radio stream", "available_playlists": list(PLAYLISTS.keys())})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
