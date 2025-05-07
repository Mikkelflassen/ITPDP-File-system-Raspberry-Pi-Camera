// static/js/gallery.js

const API = location.origin + '/api';
let videos = [];

// 1) Load & render at startup
document.addEventListener('DOMContentLoaded', loadVideos);

async function loadVideos() {
  try {
    const res = await fetch(`${API}/videos`);
    videos = await res.json();
    render();
  } catch (e) {
    console.error("Failed to fetch videos:", e);
  }
}

// 2) Build the gallery grid (no inline delete buttons here)
function render() {
  const grid = document.getElementById('grid');
  grid.innerHTML = '';

  videos.forEach(v => {
    const created = new Date(v.created_at)
      .toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric'
      });

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <video playsinline src="${API}/video/${v.slug}/stream#t=0.1" muted></video>
      <div class="meta">
        <h4>${v.title || '<em>Untitled</em>'}</h4>
        <small>${created}</small>
      </div>`;

    // open preview dialog on click
    card.addEventListener('click', () => openDlg(v));
    grid.appendChild(card);
  });
}

// 3) Preview dialog helpers

function openDlg(v) {
  // show the dialog
  const dlg = document.getElementById('dlg');
  dlg.classList.add('open');

  // populate video, title, download link
  document.getElementById('dlgVid').src = `${API}/video/${v.slug}/stream`;
  const t = document.getElementById('dlgTitle');
  t.value = v.title || '';
  t.dataset.slug = v.slug;
  const dl = document.getElementById('dlLink');
  dl.href = `${API}/video/${v.slug}/download`;
  dl.download = v.orig_name;

  // wire Save Title (existing)
  // note: saveTitle() already reads t.dataset.slug and updates videos[] + re-renders

  // wire Delete button inside dialog
  const delBtn = document.getElementById('delBtn');
  delBtn.onclick = async () => {
    if (!confirm("Are you sure you want to delete this video?")) {
      return;
    }
    try {
      const res = await fetch(`${API}/video/${v.slug}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error(res.statusText);

      // remove from local array + re-render
      videos = videos.filter(x => x.slug !== v.slug);
      render();

      // close the dialog
      closeDlg({ target: { id: 'dlg' } });
    } catch (err) {
      console.error("Delete failed:", err);
      alert("Could not delete video");
    }
  };
}

function closeDlg(ev) {
  if (ev.target.id === 'dlg') {
    document.getElementById('dlg').classList.remove('open');
  }
}

function saveTitle() {
  const t = document.getElementById('dlgTitle');
  fetch(`${API}/video/${t.dataset.slug}/title`, {
    method: 'PATCH',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({title: t.value})
  })
    .then(r => r.ok ? r.json() : Promise.reject(r))
    .then(updated => {
      videos = videos.map(v => v.slug === updated.slug ? updated : v);
      render();
      closeDlg({target:{id:'dlg'}});
    })
    .catch(err => {
      console.error("Title save failed:", err);
      alert('Could not save title');
    });
}
