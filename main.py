import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Path to cookies file (modify if needed)
COOKIES_PATH = "/mnt/data/cookies.txt"

# Ensure yt-dlp is updated
subprocess.run(["pip", "install", "--no-cache-dir", "-U", "yt-dlp"])

def get_audio_stream_url(channel_url):
    """Fetches the latest audio stream URL from a YouTube channel."""
    try:
        command = [
            "yt-dlp",
            "--get-url",
            "-f", "bestaudio",
            "--cookies", COOKIES_PATH,
            "--no-playlist",
            channel_url
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@app.route('/stream', methods=['GET'])
def stream_audio():
    """Fetches the latest audio stream URL and returns it."""
    channel_url = request.args.get("channel")
    if not channel_url:
        return jsonify({"error": "Channel URL is required"}), 400

    stream_url = get_audio_stream_url(channel_url)
    
    if stream_url.startswith("Error"):
        return jsonify({"error": stream_url}), 500

    return jsonify({"stream_url": stream_url})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)