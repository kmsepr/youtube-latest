import subprocess
import os

# Path to the cookies file
COOKIES_PATH = "/mnt/data/cookies.txt"

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
        result = subprocess.run(command, check=True, text=True, capture_output=True)

        # Print the output
        print("Download successful!")
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        # Handle errors
        print("Download failed!")
        print("Error:", e.stderr)

# Example usage
if __name__ == "__main__":
    # Replace with your YouTube URL
    youtube_url = "https://www.youtube.com/watch?v=VIDEO_ID"  # or a playlist URL

    # Optional: Specify an output path template
    # Example: "/path/to/save/%(title)s.%(ext)s"
    output_template = None

    # Download the content
    download_youtube_content(youtube_url, output_template)