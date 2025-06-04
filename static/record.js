const API = location.origin + '/api';
const btn = document.getElementById('rec');
const msg = document.getElementById('msg');

btn.onclick = async () => {
    btn.disabled = true;
    msg.textContent = 'Recording…';

    try {
        const r = await fetch(API + '/record', { method: 'POST' });
        if (!r.ok) throw new Error(await r.text());
        msg.textContent = 'Uploaded! Redirecting…';
        setTimeout(() => {
            location.href = '{{ url_for("gallery") }}';
        }, 1200);
    } catch (e) {
        msg.textContent = 'Failed: ' + e.message;
        btn.disabled = false;
    }
};
