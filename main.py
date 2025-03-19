from flask import Flask, request, jsonify
import subprocess
import os

# Path to the cookies file
COOKIES_PATH = "/mnt/data/cookies.txt"

# Create a Flask app
app = Flask(__name__)

# Function to download a video or playlist
def download_youtube_content(url, output_path=None):
    try:
        # Base command with yt-dlp
        command = [
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            url
        ]

        # Add output path if provided
        if output_path:
            command.extend(["-o", output_path])

        # Run the command
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, check=True, text=True, capture_output=True)

        # Return the output
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Handle errors from yt-dlp
        return f"Download failed! Error: {e.stderr}"
    except Exception as e:
        # Handle any other unexpected errors
        return f"An unexpected error occurred: {str(e)}"

# Define a route to trigger downloads
@app.route('/download', methods=['POST'])
def download():
    # Get the URL from the request
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    # Optional: Get the output path from the request
    output_path = data.get('output_path', "/mnt/data/downloads/%(title)s.%(ext)s")

    # Download the content
    result = download_youtube_content(url, output_path)

    # Return the result
    return jsonify({"result": result})

# Run the app
if __name__ == '__main__':
    # Bind to all interfaces (0.0.0.0) and port 5000
    app.run(host='0.0.0.0', port=5000)