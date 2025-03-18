from flask import Flask, Response, jsonify
import subprocess
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Dictionary of YouTube playlists
PLAYLISTS = {
    "playlist1": "https://www.youtube.com/playlist?list=PLWzDl-O4zlwSDM6PAMsGgFNCPsvQk-2aN",
    "playlist2": "https://youtube.com/playlist?list=PLGwUmcHSMM44vCWbO_LSLfFHKwZABQ3Ck",
}

def generate_audio(playlist_url):
    logging.info(f"Starting stream for {playlist_url}")

    # Run yt-dlp to get the best audio URL
    command = [
        "yt-dlp",
        "--force-generic-extractor",
        "-f", "91",
        "-o", "-",
        playlist_url
    ]
    logging.debug(f"yt-dlp command: {' '.join(command)}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Run ffmpeg to encode the audio
    ffmpeg_command = [
        "ffmpeg",
        "-i", "pipe:0",
        "-acodec", "libmp3lame",
        "-b:a", "64k",
        "-f", "mp3",
        "pipe:1"
    ]
    logging.debug(f"ffmpeg command: {' '.join(ffmpeg_command)}")

    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Read stderr logs from yt-dlp and ffmpeg
    for stderr_line in process.stderr:
        logging.error(f"yt-dlp error: {stderr_line.decode().strip()}")

    for stderr_line in ffmpeg_process.stderr:
        logging.error(f"ffmpeg error: {stderr_line.decode().strip()}")

    try:
        while True:
            chunk = ffmpeg_process.stdout.read(1024)
            if not chunk:
                break
            yield chunk
    except GeneratorExit:
        logging.info("Client disconnected, terminating processes.")
        process.terminate()
        ffmpeg_process.terminate()

@app.route('/stream/<playlist_key>')
def stream(playlist_key):
    playlist_url = PLAYLISTS.get(playlist_key)

    if not playlist_url:
        logging.warning(f"Invalid playlist key: {playlist_key}")
        return jsonify({"error": "Invalid playlist key. Available playlists: " + ", ".join(PLAYLISTS.keys())}), 400

    logging.info(f"Streaming playlist: {playlist_key} - {playlist_url}")
    return Response(generate_audio(playlist_url), mimetype='audio/mpeg')

@app.route('/')
def home():
    return jsonify({
        "message": "Use /stream/playlist1 or /stream/playlist2 to listen to a specific playlist",
        "available_playlists": list(PLAYLISTS.keys())
    })

if __name__ == '__main__':
    logging.info("Starting Flask app on port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)
