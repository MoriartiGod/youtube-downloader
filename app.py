from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_common_options(output):
    return {
        "outtmpl": output,
        "noplaylist": True,
        "quiet": False,

        # YouTube JavaScript challenge solving
        "js_runtimes": {
            "node": {}
        },

        # Download EJS challenge solver components
        "remote_components": {
            "ejs": ["github"]
        },
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    format_type = request.form.get("format", "mp4")
    quality = request.form.get("quality", "best")

    if not url:
        return "Введите ссылку на YouTube", 400

    file_id = str(uuid.uuid4())

    output = os.path.join(
        DOWNLOAD_DIR,
        file_id + ".%(ext)s"
    )

    common = get_common_options(output)

    if format_type == "mp3":

        options = {
            **common,

            "format": "bestaudio/best",

            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    else:

        if quality == "best":
            video_format = "bestvideo+bestaudio/best"
        else:
            video_format = (
                f"bestvideo[height<={quality}]"
                f"+bestaudio/"
                f"best[height<={quality}]"
            )

        options = {
            **common,

            "format": video_format,
            "merge_output_format": "mp4",
        }

    try:

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        files = [
            os.path.join(DOWNLOAD_DIR, filename)
            for filename in os.listdir(DOWNLOAD_DIR)
            if filename.startswith(file_id + ".")
        ]

        if not files:
            return "Файл не найден после скачивания", 500

        file_path = files[0]

        response = send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )

        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        return response

    except Exception as e:
        print(f"DOWNLOAD ERROR: {e}")
        return f"Ошибка: {str(e)}", 500


@app.route("/test-youtube")
def test_youtube():

    url = "https://www.youtube.com/watch?v=tl05LLqL2gQ"

    options = {
        "quiet": False,
        "noplaylist": True,
        "skip_download": True,

        "js_runtimes": {
            "node": {}
        },

        "remote_components": {
            "ejs": ["github"]
        },
    }

    try:

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                url,
                download=False
            )

        return {
            "ok": True,
            "title": info.get("title"),
            "height": info.get("height"),
            "formats": len(info.get("formats", []))
        }

    except Exception as e:

        print(f"TEST ERROR: {e}")

        return {
            "ok": False,
            "error": str(e)
        }, 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
