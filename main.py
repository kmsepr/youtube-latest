from flask import Flask, Response
import os
import random
import subprocess
from yt_dlp import YoutubeDL

app = Flask(__name__)

# YouTube playlist URL
PLAYLIST_URL = "https://youtube.com/playlist?list=PLMDetQy00TVmnHULOZQlJOpm39X8tIN9H"

# Directory to store downloaded audio files
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def download_playlist():
    """Download audio from the YouTube playlist."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': f'{AUDIO_DIR}/%(title)s.%(ext)s',
        'noplaylist': False,
        'quiet': True,  # Suppress yt-dlp output
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([PLAYLIST_URL])

def shuffle_audio_files():
    """Shuffle the downloaded audio files."""
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')]
    random.shuffle(audio_files)
    return audio_files

def generate_audio_stream():
    """Stream shuffled audio files."""
    audio_files = shuffle_audio_files()
    for audio_file in audio_files:
        audio_path = os.path.join(AUDIO_DIR, audio_file)
        ffmpeg_command = [
            'ffmpeg',
            '-re',  # Read input at native frame rate
            '-i', audio_path,
            '-f', 'mp3',
            '-'  # Output to stdout
        ]
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1024)
        for chunk in iter(lambda: process.stdout.read(1024), b''):
            yield chunk
        process.terminate()  # Ensure the process is terminated after streaming

@app.route('/stream')
def stream():
    """Route to stream audio."""
    download_playlist()
    return Response(generate_audio_stream(), mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)