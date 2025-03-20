import subprocess
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

COOKIES_PATH = "/mnt/data/cookies.txt"

def get_audio_stream_url(channel_url):
    """Fetch the direct audio stream URL without downloading."""
    try:
        command = [
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "-f", "bestaudio",
            "--get-url",
            channel_url
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

@app.route('/stream', methods=['GET'])
def stream_audio():
    """Streams the latest video’s audio as a live radio."""
    channel_url = request.args.get("channel")
    if not channel_url:
        return jsonify({"error": "Channel URL is required"}), 400

    stream_url = get_audio_stream_url(channel_url)
    if not stream_url:
        return jsonify({"error": "Failed to get audio stream URL"}), 500

    # Stream audio in real-time using FFmpeg
    def generate_audio():
        process = subprocess.Popen(["ffmpeg", "-i", stream_url, "-f", "mp3", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        while chunk := process.stdout.read(1024):
            yield chunk

    return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)