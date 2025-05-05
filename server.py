#!/usr/bin/env python3
import os, datetime, mimetypes, uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess, tempfile

def record_and_upload():
    """
    Record 5 s H.264 clip with libcamera on the Pi itself,
    re‑package to mp4, then call upload() internally.
    """
    TMP = Path(tempfile.gettempdir())
    h264 = TMP / "clip.h264"
    mp4  = TMP / "clip.mp4"

    # 1) capture 5 s
    subprocess.run([
        "libcamera-vid", "--width","1280","--height","720",
        "--codec","h264","-t","5000","-o",str(h264)
    ], check=True)

    # 2) wrap into mp4
    subprocess.run(["MP4Box","-add",str(h264),str(mp4)], check=True)
    h264.unlink()

    # 3) open as Werkzeug FileStorage and re‑use upload() route
    from werkzeug.datastructures import FileStorage
    with mp4.open("rb") as fp:
        file_obj = FileStorage(fp, filename="pi_clip.mp4", content_type="video/mp4")
        with app.test_request_context(
            "/api/upload", method="POST",
            data={"file": file_obj},
            content_type="multipart/form-data"
        ):
            resp, code = upload()
    mp4.unlink()
    return resp  # JSON dict from upload()

# ---------- config ----------
BASE_DIR        = Path(__file__).resolve().parent
UPLOAD_DIR      = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
DB_URI          = f"sqlite:///{BASE_DIR/'videos.db'}"  # swap for Postgres in prod
MAX_MB          = 200                                  # sane cap on upload size

# ---------- app ----------
app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI = DB_URI,
    MAX_CONTENT_LENGTH      = MAX_MB * 1024 * 1024,
)
db  = SQLAlchemy(app)
CORS(app)                               # allow phone browser on same subnet

# ---------- model ----------
class Video(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    slug      = db.Column(db.String, unique=True, nullable=False)
    orig_name = db.Column(db.String, nullable=False)
    title     = db.Column(db.String, nullable=True)                 # NEW
    mime      = db.Column(db.String, nullable=False)
    bytes     = db.Column(db.Integer, nullable=False)
    created_at= db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def as_dict(self):
        return dict(
            id=self.id,
            slug=self.slug,
            orig_name=self.orig_name,
            title=self.title,
            mime=self.mime,
            size=self.bytes,
            created_at=self.created_at.isoformat() + "Z"
        )      # ← this closing parenthesis was missing



# ---------- endpoints ----------
# ---------- front‑end ----------
@app.route("/")
def gallery():
    return render_template("gallery.html")

# control / record page you uploaded
@app.route("/control")
def control():
    return render_template("front_page.html")   # your uploaded layout

# one‑tap record page
@app.route("/record")
def record_page():
    return render_template("front_page.html")

@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return {"error": "No file part"}, 400
    f        = request.files["file"]
    if f.filename == "":
        return {"error": "Empty filename"}, 400
    slug     = uuid.uuid4().hex
    safe_ext = Path(f.filename).suffix
    fname    = f"{slug}{safe_ext}"
    path     = UPLOAD_DIR / fname
    f.save(path)

    video = Video(
        slug      = slug,
        orig_name = f.filename,
        mime      = mimetypes.guess_type(fname)[0] or "video/mp4",
        bytes     = path.stat().st_size,
    )
    db.session.add(video); db.session.commit()
    return video.as_dict(), 201

@app.route("/api/videos")
def list_videos():
    vids = Video.query.order_by(Video.created_at.desc()).all()
    return jsonify([v.as_dict() for v in vids])

@app.route("/api/record", methods=["POST"])
def record_api():
    try:
        new_clip = record_and_upload()   # JSON dict
        return new_clip, 201
    except Exception as e:
        app.logger.exception("record failed")
        return {"error": str(e)}, 500


def _send_range(path, mime):
    """Minimal HTTP Range implementation for smooth mobile scrubbing."""
    range_h = request.headers.get('Range')
    if not range_h:
        return send_file(path, mimetype=mime)
    size   = path.stat().st_size
    start  = int(range_h.replace("bytes=", "").split("-")[0])
    length = size - start
    with open(path, 'rb') as fp:
        fp.seek(start)
        data = fp.read()
    rv = app.response_class(data,
                            206,
                            mimetype=mime,
                            direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {start}-{size-1}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    return rv

@app.route("/api/video/<slug>/stream")
def stream(slug):
    v = Video.query.filter_by(slug=slug).first_or_404()
    path = UPLOAD_DIR / f"{slug}{Path(v.orig_name).suffix}"
    return _send_range(path, v.mime)

# -------- title‑edit endpoint --------
@app.route("/api/video/<slug>/title", methods=["PATCH"])
def set_title(slug):
    data = request.get_json(force=True)
    new_title = (data.get("title") or "").strip()
    if not new_title:
        return {"error": "title required"}, 400
    v = Video.query.filter_by(slug=slug).first_or_404()
    v.title = new_title
    db.session.commit()
    return v.as_dict()


@app.route("/api/video/<slug>/download")
def download(slug):
    v = Video.query.filter_by(slug=slug).first_or_404()
    path = UPLOAD_DIR / f"{slug}{Path(v.orig_name).suffix}"
    return send_file(path,
                     mimetype=v.mime,
                     as_attachment=True,
                     download_name=v.orig_name)

# ---------- one‑time init ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)
