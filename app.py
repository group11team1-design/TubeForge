from flask import Flask
from flask_cors import CORS, render_template, request, jsonify, send_from_directory
import os
import signal
import time
import threading
import uuid
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)
# Public frontend support. Restrict this with ALLOWED_ORIGINS in production if desired.
CORS(app, origins=os.environ.get('ALLOWED_ORIGINS', '*').split(','), supports_credentials=False)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

jobs = {}
cancel_events = {}


def human_size(n):
    if not n:
        return "Unknown"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024


def progress_hook(job_id):
    def hook(data):
        event = cancel_events.get(job_id)
        if event and event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")

        if data["status"] == "downloading":
            done = data.get("downloaded_bytes", 0) or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            speed = data.get("speed") or 0
            eta = data.get("eta")

            jobs[job_id].update(
                status="downloading",
                progress=round(done * 100 / total, 1) if total else 0,
                downloaded=human_size(done),
                total=human_size(total),
                speed=f"{human_size(speed)}/s" if speed else "—",
                eta=f"{eta}s" if eta is not None else "—",
            )

        elif data["status"] == "finished":
            jobs[job_id].update(
                status="processing",
                progress=100,
                eta="Processing..."
            )

    return hook


def worker(job_id, url, media_format, height):
    jobs[job_id] = {
        "status": "starting",
        "progress": 0,
        "downloaded": "0 B",
        "total": "Unknown",
        "speed": "—",
        "eta": "—",
        "filename": None,
        "error": None,
    }
    cancel_events[job_id] = threading.Event()

    try:
        common = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [progress_hook(job_id)],
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "continuedl": True,
            "concurrent_fragment_downloads": 4,
            "ffmpeg_location": FFMPEG_EXE,
            "quiet": True,
            "no_warnings": False,
        }

        if media_format == "mp3":
            opts = {
                **common,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        elif media_format == "audio":
            opts = {
                **common,
                "format": "bestaudio/best",
            }
        elif height == "best":
            opts = {
                **common,
                "format": "bestvideo*+bestaudio/best",
                "merge_output_format": "mp4",
            }
        else:
            h = int(height)
            opts = {
                **common,
                "format": f"bestvideo[height<={h}]+bestaudio/best[height<={h}]",
                "merge_output_format": "mp4",
            }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)

        if cancel_events[job_id].is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")

        files = []
        for name in os.listdir(DOWNLOAD_DIR):
            path = os.path.join(DOWNLOAD_DIR, name)
            if os.path.isfile(path):
                files.append((os.path.getmtime(path), name))

        jobs[job_id].update(
            status="complete",
            progress=100,
            filename=max(files)[1] if files else None,
            eta="Done",
        )

    except Exception as exc:
        cancelled = cancel_events[job_id].is_set()
        jobs[job_id].update(
            status="cancelled" if cancelled else "error",
            error="Download cancelled." if cancelled else str(exc),
        )
    finally:
        cancel_events.pop(job_id, None)


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="TubeForge API")


@app.post("/api/shutdown")
def shutdown_app():
    """Stop the local TubeForge process after the browser page is closed."""
    def stop_server():
        time.sleep(0.4)
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=stop_server, daemon=True).start()
    return jsonify(status="shutting_down")


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.post("/api/info")
def info():
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify(error="Enter a video URL."), 400

    try:
        options = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "ffmpeg_location": FFMPEG_EXE,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info_data = ydl.extract_info(url, download=False)

        qualities = {}
        for fmt in info_data.get("formats", []):
            if fmt.get("vcodec") != "none" and fmt.get("height"):
                height = int(fmt["height"])
                fps = float(fmt.get("fps") or 0)
                qualities[height] = max(qualities.get(height, 0), fps)

        quality_list = [
            {
                "height": height,
                "label": f"{height}p" + (
                    f" {int(fps)}fps" if fps >= 50 else ""
                ),
            }
            for height, fps in sorted(qualities.items(), reverse=True)
        ]

        return jsonify(
            title=info_data.get("title"),
            thumbnail=info_data.get("thumbnail"),
            duration=info_data.get("duration_string"),
            uploader=info_data.get("uploader"),
            qualities=quality_list,
        )

    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/download")
def download():
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify(error="Enter a video URL."), 400

    job_id = str(uuid.uuid4())
    thread = threading.Thread(
        target=worker,
        args=(
            job_id,
            url,
            data.get("format", "video"),
            data.get("height", "best"),
        ),
        daemon=True,
    )
    thread.start()

    return jsonify(job_id=job_id)


@app.get("/api/status/<job_id>")
def status(job_id):
    return jsonify(jobs.get(job_id, {"status": "unknown", "progress": 0}))


@app.post("/api/cancel/<job_id>")
def cancel(job_id):
    if job_id not in cancel_events:
        return jsonify(error="Download is no longer running."), 404

    cancel_events[job_id].set()
    jobs[job_id]["status"] = "cancelling"
    return jsonify(ok=True)


@app.get("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    # Debug/reloader is intentionally disabled for the one-click desktop launcher.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False, use_reloader=False)
