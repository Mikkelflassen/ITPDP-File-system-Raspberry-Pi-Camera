#!/usr/bin/env python3
import os, datetime, mimetypes, uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

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
    id          = db.Column(db.Integer, primary_key=True)
    slug        = db.Column(db.String,  unique=True, nullable=False)
    orig_name   = db.Column(db.String,  nullable=False)
    mime        = db.Column(db.String,  nullable=False)
    bytes       = db.Column(db.Integer, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def as_dict(self):
        return dict(
            id=self.id,
            slug=self.slug,
            orig_name=self.orig_name,
            mime=self.mime,
            size=self.bytes,
            created_at=self.created_at.isoformat() + "Z"
        )

# ---------- endpoints ----------
# ---------- front‑end ----------
@app.route("/")
def root():
    """
    Serve static/index.html when the browser asks for `/`.
    Flask automatically looks in the folder called `static`
    that sits next to this file.
    """
    return app.send_static_file("index.html")


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
