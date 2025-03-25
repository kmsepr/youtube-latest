import os
import subprocess
import time
import threading
import random
from flask import Flask, Response, jsonify

app = Flask(__name__)

# 📌 Hardcoded YouTube Video Links (Manually Updated)
STATIONS = {
    "modern_history": [
        "https://www.youtube.com/watch?v=ASnGYrBanlA",
"https://www.youtube.com/watch?v=PrUn1sf3WFk",
"https://www.youtube.com/watch?v=3Da14COqSwk",
"https://www.youtube.com/watch?v=RE5Em_Hg7dA",
"https://www.youtube.com/watch?v=4nl1Z6xUOyY",
"https://www.youtube.com/watch?v=rUUl5RUnQcw",
"https://www.youtube.com/watch?v=_RnQCC6Df6Q",
"https://www.youtube.com/watch?v=CAYIYngTRPE",
"https://www.youtube.com/watch?v=v3KKpyDGNN4",
"https://www.youtube.com/watch?v=YeS-tPwMtW0",
"https://www.youtube.com/watch?v=kUv_7SNi600",
"https://www.youtube.com/watch?v=fsiES3-Kpzg",
"https://www.youtube.com/watch?v=chtF4uVVVpU",
"https://www.youtube.com/watch?v=mD6ywrXmC8Y",
"https://www.youtube.com/watch?v=iALuBSFRJl4"
    ],
    "studyiq_history": [
        "https://www.youtube.com/watch?v=XbHmJ-qvamo",
"https://www.youtube.com/watch?v=D1k5E62J8Ts",
"https://www.youtube.com/watch?v=TQ3RVpVUkKM",
"https://www.youtube.com/watch?v=t4akLJPv0Io",
"https://www.youtube.com/watch?v=DI15B8TVRIA",
"https://www.youtube.com/watch?v=JpDr0htWizY",
"https://www.youtube.com/watch?v=EZngWp2LR0c",
"https://www.youtube.com/watch?v=4Cv7h3tXNq8",
"https://www.youtube.com/watch?v=L_Hwx8U3Dj8",
"https://www.youtube.com/watch?v=Nip4EQnLzyE",
"https://www.youtube.com/watch?v=K27eTLnSobQ",
"https://www.youtube.com/watch?v=GtiSwEtnYuw",
"https://www.youtube.com/watch?v=IljBwgJ2yYU",
"https://www.youtube.com/watch?v=8jNQEeVd5vg",
"https://www.youtube.com/watch?v=IsNFikjRVsI",
"https://www.youtube.com/watch?v=wEOEjyCsat4",
"https://www.youtube.com/watch?v=DpN4h_5qqiA",
"https://www.youtube.com/watch?v=2aG1OkuwSvQ",
"https://www.youtube.com/watch?v=anV-TTWV0l8",
"https://www.youtube.com/watch?v=d3zR0hAx99U",
"https://www.youtube.com/watch?v=EXdgtjBM9Tw",
"https://www.youtube.com/watch?v=edl1h_shi4w",
"https://www.youtube.com/watch?v=ySmHYmbwZf8",
"https://www.youtube.com/watch?v=Et4re3pGMkE",
"https://www.youtube.com/watch?v=uszABNRQ56Q",
"https://www.youtube.com/watch?v=qpKILrroPUg",
"https://www.youtube.com/watch?v=FOziQo-BHgA",
"https://www.youtube.com/watch?v=-QrPzhohCO0",
"https://www.youtube.com/watch?v=vXqVlNCd074",
"https://www.youtube.com/watch?v=xZXq5Fl9nyw",
"https://www.youtube.com/watch?v=ggdtrQ5seB4",
"https://www.youtube.com/watch?v=8sBRGHtljbY",
"https://www.youtube.com/watch?v=x5szUdlDMnA",
"https://www.youtube.com/watch?v=1sw_enRoDw0",
"https://www.youtube.com/watch?v=yC4zRN96HFU",
"https://www.youtube.com/watch?v=HF-uiMD1Fe4",
"https://www.youtube.com/watch?v=4iZrt2u10I4",
"https://www.youtube.com/watch?v=HaYpoc2uyWY",
"https://www.youtube.com/watch?v=_QqdqCvQDGM",
"https://www.youtube.com/watch?v=R8NIzJqYQtQ",
"https://www.youtube.com/watch?v=gIr4m9Sgzz8",
"https://www.youtube.com/watch?v=TNx93H1fUuQ",
"https://www.youtube.com/watch?v=5RksYnA4wTA"
    ],
    "zaytuna_2k25": [
        "https://www.youtube.com/watch?v=NHO6loh7WAQ",
"https://www.youtube.com/watch?v=5PsYf6qrj08",
"https://www.youtube.com/watch?v=GaPs57m2jgs",
"https://www.youtube.com/watch?v=hueTpFFhhUo",
"https://www.youtube.com/watch?v=e1X4Jnwsi4Q",
"https://www.youtube.com/watch?v=WUwyatwM8tI",
"https://www.youtube.com/watch?v=7ICL6iteYy4",
"https://www.youtube.com/watch?v=MCHkjxghMtU"
    ],
    "seera_malayalam": [
        "https://www.youtube.com/watch?v=HLPDazstsVg",
        "https://www.youtube.com/watch?v=m5W18O-dzcE",
        "https://www.youtube.com/watch?v=4vqYeUMSCdo",
        "https://www.youtube.com/watch?v=jFVmwbOsF0A",
        "https://www.youtube.com/watch?v=_a_6ZqS_D7w",
        "https://www.youtube.com/watch?v=Y4LQcqAIm80",
        "https://www.youtube.com/watch?v=ZVPEQ7dm5T4",
        "https://www.youtube.com/watch?v=8EYVS5q2kG4",
        "https://www.youtube.com/watch?v=H1wLLSRk5wc",
        "https://www.youtube.com/watch?v=KQWsa8xrNSA",
        "https://www.youtube.com/watch?v=Myn_UJluFds",
        "https://www.youtube.com/watch?v=CNgikkbqs-Y",
        "https://www.youtube.com/watch?v=ANN9q_L-K5U",
        "https://www.youtube.com/watch?v=gn76G53GEEg",
        "https://www.youtube.com/watch?v=swb77PkXgv4",
        "https://www.youtube.com/watch?v=0LL6QBX1pt0",
        "https://www.youtube.com/watch?v=PPJFWjJlktc",
        "https://www.youtube.com/watch?v=5tVrJcXMEkg",
        "https://www.youtube.com/watch?v=IAMlbfZzmWY",
        "https://www.youtube.com/watch?v=Sgkyj8Qvz7g",
        "https://www.youtube.com/watch?v=gSZG93h_dD4",
        "https://www.youtube.com/watch?v=pqaadVW7LNo",
        "https://www.youtube.com/watch?v=qc-HAE3zvcg",
        "https://www.youtube.com/watch?v=9ncceOVjyPs",
        "https://www.youtube.com/watch?v=JNPd83D4IVM",
        "https://www.youtube.com/watch?v=keFyTf2Sjug",
        "https://www.youtube.com/watch?v=Z_hGGve9Pp4",
        "https://www.youtube.com/watch?v=IOG1Kg4k9iE",
        "https://www.youtube.com/watch?v=hVMlMwSwJvU",
        "https://www.youtube.com/watch?v=Ozo-DQXHVhc",
        "https://www.youtube.com/watch?v=BtpbKO5N7xU",
        "https://www.youtube.com/watch?v=KfUKded8o0I",
        "https://www.youtube.com/watch?v=bDd8QjUObNk",
        "https://www.youtube.com/watch?v=Y84coAaQUc4",
        "https://www.youtube.com/watch?v=myYEf6TE5y4",
        "https://www.youtube.com/watch?v=pGwpFARV4-8",
        "https://www.youtube.com/watch?v=7RIvHRvgqvQ",
        "https://www.youtube.com/watch?v=8BoHLfPCSJs",
        "https://www.youtube.com/watch?v=xmrEgcA4vuw",
        "https://www.youtube.com/watch?v=p2BnQnBLBqA",
        "https://www.youtube.com/watch?v=Pz5Kt_fx284",
        "https://www.youtube.com/watch?v=M-YyCXkeOp0",
        "https://www.youtube.com/watch?v=BSBu9uIN7mw",
        "https://www.youtube.com/watch?v=L3vQzcWExF8",
        "https://www.youtube.com/watch?v=y3rs0UX3ZzM",
        "https://www.youtube.com/watch?v=nrPFIwMa7Ko",
        "https://www.youtube.com/watch?v=lCI05atVAEc",
        "https://www.youtube.com/watch?v=GejhjQjDiLI",
        "https://www.youtube.com/watch?v=XPvQ8u7Bo5M",
        "https://www.youtube.com/watch?v=pnbAbFADFNw",
        "https://www.youtube.com/watch?v=IBu7SEZkesU",
        "https://www.youtube.com/watch?v=xSB7uefOdZw",
        "https://www.youtube.com/watch?v=LeyUsBHJQ58",
        "https://www.youtube.com/watch?v=x5oVHFayUQk",
        "https://www.youtube.com/watch?v=5LvT-x1DGkQ",
        "https://www.youtube.com/watch?v=9HaGVVAVYTc",
        "https://www.youtube.com/watch?v=1vK5Q0aQTc0",
        "https://www.youtube.com/watch?v=XLYNnWtCxLI",
        "https://www.youtube.com/watch?v=QjcPveLmWQ0",
        "https://www.youtube.com/watch?v=qSsfjsWlKpA",
        "https://www.youtube.com/watch?v=L-XeIe12wjs",
        "https://www.youtube.com/watch?v=vMn2e7_13uE",
        "https://www.youtube.com/watch?v=YvJUAftqjbg",
        "https://www.youtube.com/watch?v=GcDpl8OfDWo",
        "https://www.youtube.com/watch?v=BrCXaTYMm3U",
        "https://www.youtube.com/watch?v=oZ7Hpnt4LsA",
        "https://www.youtube.com/watch?v=tDIUwbadTNQ",
        "https://www.youtube.com/watch?v=G85iLYune9k",
        "https://www.youtube.com/watch?v=I7mEnM3STEs",
        "https://www.youtube.com/watch?v=8Y1j9a4p0WM",
        "https://www.youtube.com/watch?v=s3Bh-c1sUqY",
        "https://www.youtube.com/watch?v=xSfj9nYF1lE",
        "https://www.youtube.com/watch?v=dVq4uR51pak",
        "https://www.youtube.com/watch?v=YRDCheQggBs",
        "https://www.youtube.com/watch?v=JubGnY05y2E",
        "https://www.youtube.com/watch?v=ooL0dwED9ps",
        "https://www.youtube.com/watch?v=yig9bhSTIGM",
        "https://www.youtube.com/watch?v=fGrTAlEHrCo",
        "https://www.youtube.com/watch?v=J-UI8rlsjjs",
        "https://www.youtube.com/watch?v=seINc53QaRc",
        "https://www.youtube.com/watch?v=wk5BoXefxi0",
        "https://www.youtube.com/watch?v=70ZyBLGl0QM",
        "https://www.youtube.com/watch?v=aKFXVvjNfS0",
        "https://www.youtube.com/watch?v=25p49yXGBoU",
        "https://www.youtube.com/watch?v=it5S3snmynk",
        "https://www.youtube.com/watch?v=2Xg5LFjnC0s",
        "https://www.youtube.com/watch?v=pMlzQjKkCNk",
        "https://www.youtube.com/watch?v=jVXkUbxEWWk",
        "https://www.youtube.com/watch?v=PGUjomCGD8E",
        "https://www.youtube.com/watch?v=EDePFnWqQs8",
        "https://www.youtube.com/watch?v=aPJ-H0Uv5E4",
        "https://www.youtube.com/watch?v=JyA2nsCrgHI",
        "https://www.youtube.com/watch?v=PC7X6chVtkc",
        "https://www.youtube.com/watch?v=LVjjBBF2ZjA",
        "https://www.youtube.com/watch?v=ELQ4GlaJIe4",
        "https://www.youtube.com/watch?v=yYtbgfa4Ouc",
        "https://www.youtube.com/watch?v=J5Ti5sOL-Ww",
        "https://www.youtube.com/watch?v=p6LrJ8LLnfE",
        "https://www.youtube.com/watch?v=uS86C68wYgI",
        "https://www.youtube.com/watch?v=xrOEOz9UdEg",
        "https://www.youtube.com/watch?v=HJMcmLEXQU4",
        "https://www.youtube.com/watch?v=jG4V3BXBdfQ"
    ]
}

stream_cache = {}
cache_lock = threading.Lock()

def extract_audio_url(video_url):
    """Extract direct audio URL using yt-dlp."""
    command = [
        "yt-dlp", "--cookies", "/mnt/data/cookies.txt",
        "-f", "bestaudio",
        "-g", video_url
    ]
    print(f"Extracting audio from: {video_url}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        audio_url = result.stdout.strip()
        if audio_url:
            return audio_url
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract audio: {e}")

    return None

def refresh_stream_urls():
    """Refresh stream URLs when needed."""
    while True:
        with cache_lock:
            for station, video_list in STATIONS.items():
                video_url = random.choice(video_list)  # Pick a random video from the list
                audio_url = extract_audio_url(video_url)

                if audio_url:
                    stream_cache[station] = audio_url
                    print(f"Updated cache for {station}: {audio_url}")

        time.sleep(1800)  # Refresh URLs every 30 minutes
def detect_looping(process):
    """Detect looping by checking the current playback time."""
    last_position = None

    while True:
        try:
            position_command = ["ffmpeg", "-i", "-", "-vn", "-af", "ashowinfo", "-f", "null", "-"]
            result = subprocess.run(position_command, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                output = result.stderr
                position_lines = [line for line in output.split("\n") if "pts_time:" in line]
                if position_lines:
                    latest_position = float(position_lines[-1].split("pts_time:")[-1].strip())

                    if last_position is not None and latest_position < last_position:
                        print("⚠️ Looping detected! Refreshing stream...")
                        return True

                    last_position = latest_position

            time.sleep(5)  # Check every 5 seconds

        except Exception as e:
            print(f"Error detecting looping: {e}")
            return False

def generate_stream(station_name):
    """Continuously stream audio and refresh when looping is detected."""
    while True:
        with cache_lock:
            stream_url = stream_cache.get(station_name)

        if not stream_url:
            print(f"Fetching new stream for {station_name}...")
            video_url = random.choice(STATIONS[station_name])
            stream_url = extract_audio_url(video_url)

            if stream_url:
                with cache_lock:
                    stream_cache[station_name] = stream_url

        if not stream_url:
            print(f"No valid stream URL for {station_name}, retrying in 10s...")
            time.sleep(10)
            continue

        print(f"Streaming from: {stream_url}")

        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-http_persistent", "0",  
                "-i", stream_url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        if detect_looping(process):  # If looping detected, restart stream
            process.kill()
            continue

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except (GeneratorExit, Exception):
            print(f"Stream error for {station_name}, restarting stream...")
            process.kill()
            time.sleep(5)
            continue

@app.route("/play/<station_name>")
def stream(station_name):
    if station_name not in STATIONS:
        return jsonify({"error": "Station not found"}), 404

    return Response(generate_stream(station_name), mimetype="audio/mpeg")

threading.Thread(target=refresh_stream_urls, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)