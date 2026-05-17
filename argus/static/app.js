const ICONS = {
    webcam: '📹',
    audio: '🎤',
    screen: '🖥️',
    system: '🧠',
    thermal: '🌡️',
    environmental: '🌬️',
    gps: '📍',
    default: '🔌'
};

let sensors = {};
let sseConnections = {};

async function loadSensors() {
    const res = await fetch('/api/status');
    const data = await res.json();
    const grid = document.getElementById('sensor-grid');
    grid.innerHTML = '';

    if (data.available.length === 0) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align:center; padding:3rem;">No sensors detected.</p>';
        return;
    }

    for (const s of data.available) {
        sensors[s.name] = s;
        const card = document.createElement('div');
        card.className = 'sensor-card';
        card.id = `card-${s.name}`;
        card.innerHTML = `
            <h2><span class="icon">${ICONS[s.name] || ICONS.default}</span> ${s.name}</h2>
            <div class="capabilities">${s.capabilities.map(c => `<span class="cap">${c}</span>`).join('')}</div>
            <div class="actions">
                <button onclick="readSensor('${s.name}')">Read</button>
                ${s.capabilities.includes('stream') ? `<button onclick="toggleStream('${s.name}')" id="stream-btn-${s.name}">Stream</button>` : ''}
                ${s.capabilities.includes('capture') ? `<a href="/api/${s.name}/image" target="_blank">Image</a>` : ''}
                ${s.capabilities.includes('capture') && s.name === 'audio' ? `<a href="/api/${s.name}/audio" target="_blank">Audio</a>` : ''}
            </div>
            <div class="preview" id="preview-${s.name}"></div>
        `;
        grid.appendChild(card);
    }

    updateStatus(true);
}

async function readSensor(name) {
    const preview = document.getElementById(`preview-${name}`);
    preview.style.display = 'block';
    preview.innerHTML = '<pre>Loading...</pre>';

    try {
        const res = await fetch(`/api/${name}/read`);
        const data = await res.json();
        const payload = typeof data === 'string' ? JSON.parse(data) : data;

        let html = '';
        if (payload.error) {
            html = `<pre style="color:var(--error)">Error: ${payload.error}</pre>`;
        } else {
            if (payload.image_b64) {
                html += `<img src="data:image/jpeg;base64,${payload.image_b64}" alt="${name}">`;
            }
            if (payload.text) {
                html += `<pre>${escapeHtml(payload.text)}</pre>`;
            }
            if (payload.data && Object.keys(payload.data).length > 0 && !payload.image_b64) {
                html += `<pre>${JSON.stringify(payload.data, null, 2)}</pre>`;
            }
        }
        preview.innerHTML = html;
    } catch (e) {
        preview.innerHTML = `<pre style="color:var(--error)">Fetch error: ${e.message}</pre>`;
    }
}

function toggleStream(name) {
    const btn = document.getElementById(`stream-btn-${name}`);
    const card = document.getElementById(`card-${name}`);

    if (sseConnections[name]) {
        sseConnections[name].close();
        delete sseConnections[name];
        btn.textContent = 'Stream';
        card.classList.remove('streaming');
        return;
    }

    const preview = document.getElementById(`preview-${name}`);
    preview.style.display = 'block';
    preview.innerHTML = '<pre>Streaming...</pre>';

    const es = new EventSource(`/api/${name}/stream`);
    sseConnections[name] = es;
    btn.textContent = 'Stop';
    card.classList.add('streaming');

    es.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            let html = '';
            if (payload.image_b64) {
                html = `<img src="data:image/jpeg;base64,${payload.image_b64}" alt="${name}">`;
            } else if (payload.text) {
                html = `<pre>${escapeHtml(payload.text)}</pre>`;
            } else {
                html = `<pre>${JSON.stringify(payload.data, null, 2)}</pre>`;
            }
            preview.innerHTML = html;
        } catch (e) {
            preview.innerHTML = `<pre>${escapeHtml(event.data)}</pre>`;
        }
    };

    es.onerror = () => {
        preview.innerHTML += '<pre style="color:var(--error)">SSE error</pre>';
        toggleStream(name);
    };
}

function updateStatus(connected) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (connected) {
        dot.classList.remove('offline');
        text.textContent = `${Object.keys(sensors).length} senses active`;
    } else {
        dot.classList.add('offline');
        text.textContent = 'Disconnected';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Init
loadSensors();
setInterval(() => {
    // Re-check status every 10s
    fetch('/api/status')
        .then(r => r.json())
        .then(d => updateStatus(true))
        .catch(() => updateStatus(false));
}, 10000);
