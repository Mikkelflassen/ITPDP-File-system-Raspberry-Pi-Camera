import subprocess, datetime, requests, pathlib, os

SERVER = "http://your-server-ip:8000/api/upload"   # adjust
CLIP_SEC = 10

def record_clip(tmp="clip.h264"):
    subprocess.check_call([
        "libcamera-vid",
        "-t", str(CLIP_SEC * 1000),
        "-o", tmp
    ])
    # Convert to MP4 container so browsers like it
    mp4 = pathlib.Path(f"clip_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4")
    subprocess.check_call(["MP4Box", "-add", tmp, mp4])
    os.remove(tmp)
    return mp4

def upload(path):
    with open(path, "rb") as fp:
        r = requests.post(SERVER, files={"file": fp})
        r.raise_for_status()
    print("Uploaded", r.json())

if __name__ == "__main__":
    clip = pathlib.Path("/Users/mikkel/Desktop/WebOfThings/Assignment6-video7.mp4")   # <— any small MP4
    upload(clip)
