

const recordBtn = document.getElementById("btnRecord");
const trackBtn = document.getElementById("btnTrack");
let recording = false;
let tracking = false;
document.addEventListener('DOMContentLoaded', () => {
  recording = localStorage.getItem("recording");
  tracking = localStorage.getItem("tracking")
});

console.log(localStorage.getItem("recording"))
recordBtn.onclick = async () => {
  recordBtn.disabled = true;
  const url = recording ? "/api/stop-record" : "/api/record";
  try {
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) throw new Error(res.statusText);
    recording = !recording;
    localStorage.setItem("recording", recording);
    recordBtn.classList.toggle("active", recording);
  } catch (e) {
    console.error("Record error:", e);
  } finally {
    recordBtn.disabled = false;
  }
};

trackBtn.onclick = async () => {
  trackBtn.disabled = true;
  const url = tracking ? "/api/stop-track" : "/api/track";
  try {
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) throw new Error(res.statusText);
    tracking = !tracking;
    localStorage.setItem("tracking", tracking);
    trackBtn.classList.toggle("active", tracking);
  } catch (e) {
    console.error("Track error:", e);
  } finally {
    trackBtn.disabled = false;
  }
};

