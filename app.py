from flask import Flask, Response, jsonify
import subprocess

app = Flask(__name__)

YOUTUBE_PLAYLIST = "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN"

def generate_audio():
    command = f'yt-dlp -f "bestaudio" -o - "{YOUTUBE_PLAYLIST}" | ffmpeg -i - -acodec libmp3lame -b:a 128k -f mp3 -'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    while True:
        chunk = process.stdout.read(1024)
        if not chunk:
            break
        yield chunk
    process.terminate()

@app.route('/stream')
def stream():
    return Response(generate_audio(), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({"message": "Go to /stream to listen to the radio stream"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
