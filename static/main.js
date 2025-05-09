// static/js/gallery.js

document.addEventListener('DOMContentLoaded', () => {
  const recordBtn = document.getElementById("btnRecord");
  const trackBtn = document.getElementById("btnTrack");

  // ── 1) Page-load init from localStorage ────────────────────────
  let recording = localStorage.getItem("recording") === "true";
  let tracking = localStorage.getItem("tracking") === "true";

  // apply the active class if needed
  recordBtn.classList.toggle("active", recording);
  trackBtn.classList.toggle("active", tracking);

  // ── 2) toggle helper ──────────────────────────────────────────
  async function toggle(btn, flag, onPath, offPath, storageKey) {
    btn.disabled = true;
    const url = flag ? offPath : onPath;
    try {
      const res = await fetch(url, { method: "POST" });
      if (!res.ok) throw new Error(res.statusText);
      flag = !flag;
      localStorage.setItem(storageKey, flag);
      btn.classList.toggle("active", flag);
    } catch (e) {
      console.error(e);
    } finally {
      btn.disabled = false;
    }
    return flag;
  }

  // ── 3) Button click handlers ───────────────────────────────────
  recordBtn.onclick = async () => {
    recording = await toggle(
      recordBtn,
      recording,
      "/api/record",
      "/api/stop-record",
      "recording"
    );
  };

  trackBtn.onclick = async () => {
    tracking = await toggle(
      trackBtn,
      tracking,
      "/api/track",
      "/api/stop-track",
      "tracking"
    );
  };
});
