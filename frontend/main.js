const el = (id) => document.getElementById(id);

// --- Navigation Handling ---
function setActiveTab(activeId) {
  // Remove active class from all nav buttons
  document.querySelectorAll('nav button').forEach(btn => btn.classList.remove('active'));
  // Add active class to clicked button
  const btn = el('tab-' + activeId);
  if (btn) btn.classList.add('active');
}

el('tab-upload').onclick = () => { showPanel('upload'); setActiveTab('upload'); };
el('tab-uploads').onclick = () => { showPanel('uploads'); setActiveTab('uploads'); loadUploads(); };
el('tab-db').onclick = () => { showPanel('db'); setActiveTab('db'); loadDB(); };

function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.style.display = 'none');
  el('panel-' + name).style.display = '';
}

// --- Helpers ---
async function fetchJson(path, opts) {
  const res = await fetch(path, opts);
  if (res.ok) return res.json();
  
  let errText = '';
  try {
    const j = await res.json();
    errText = j.detail || JSON.stringify(j);
  } catch (e) {
    errText = await res.text();
  }
  
  if (res.status === 503 && String(errText).toLowerCase().includes('database')) {
    throw new Error('Database unavailable — try again later');
  }
  throw new Error(errText || res.statusText || `HTTP ${res.status}`);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
}

// Simple syntax highlighter for logs
function colorizeLog(line) {
    const lower = line.toLowerCase();
    let className = 'log-line';
    if (lower.includes('error') || lower.includes('fail')) className = 'log-err';
    else if (lower.includes('warn')) className = 'log-warn';
    else if (lower.includes('info')) className = 'log-info';
    
    // Wrap timestamp if it exists at start (regex assumption for ISO-ish dates)
    return `<div class="${className}">${line}</div>`;
}

// --- Upload Logic ---
el('upload-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const fileInput = el('file-input');
  const resultBox = el('upload-result');
  const resultContainer = el('upload-result-container');
  const submitBtn = el('upload-form').querySelector('button');

  if (!fileInput.files.length) return alert('Please choose a file first');

  // UI Loading State
  submitBtn.disabled = true;
  submitBtn.textContent = 'Uploading...';
  resultContainer.style.display = 'block';
  resultBox.textContent = 'Processing...';

  const form = new FormData();
  form.append('file', fileInput.files[0]);

  try {
    const data = await fetchJson('/upload', { method: 'POST', body: form });
    resultBox.textContent = JSON.stringify(data, null, 2);
    // Auto-refresh uploads list if we switch tabs later
  } catch (err) {
    resultBox.innerHTML = `<span style="color:var(--danger)">${String(err)}</span>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Start Upload';
  }
});

// --- History / Ingests Logic ---
async function loadUploads() {
  const list = el('uploads-list');
  list.innerHTML = '<li style="color:var(--text-muted)">Loading history...</li>';
  
  try {
    const items = await fetchJson('/api/ingests');
    list.innerHTML = '';
    
    if(items.length === 0) {
        list.innerHTML = '<li style="color:var(--text-muted)">No uploads found.</li>';
        return;
    }

    items.forEach(it => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span>
            <strong>${it.file_name || 'Unknown'}</strong><br>
            <small style="color:var(--text-muted)">${formatDate(it.created_at)}</small>
        </span>
        <span class="badge badge-success">${it.inserted_rows} rows</span>
      `;
      li.dataset.id = it.id;
      li.onclick = () => {
        // Simple visual active state for list items
        document.querySelectorAll('#uploads-list li').forEach(i => i.style.background = 'transparent');
        li.style.background = '#f3f4f6';
        loadFileViewer(it.id);
      };
      list.appendChild(li);
    });
  } catch (err) {
    list.innerHTML = `<li style="color:var(--danger)">Error: ${err}</li>`;
  }
}

async function loadFileViewer(id) {
  const container = el('file-content');
  container.innerHTML = '<div style="padding:1rem">Loading logs...</div>';
  
  try {
    const rows = await fetchJson(`/api/ingests/${id}/logs?limit=500`);
    if(!rows || rows.length === 0) {
        container.textContent = 'No logs found in this file.';
        return;
    }
    
    // Map rows to HTML with color highlighting
    const htmlLines = rows.map(r => {
        const text = `${r.timestamp || ''} [${r.level || 'UNK'}] ${r.module || ''} - ${r.message || ''}`;
        return colorizeLog(text);
    }).join('');
    
    container.innerHTML = htmlLines;
  } catch (err) {
    container.innerHTML = `<div style="color:var(--danger)">Error loading file: ${err}</div>`;
  }
}

// --- DB Explorer Logic ---
async function loadDB() {
  const tbody = document.querySelector('#db-table tbody');
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">Loading data...</td></tr>';
  
  try {
    const items = await fetchJson('/api/ingests');
    tbody.innerHTML = '';
    items.forEach(it => {
      const tr = document.createElement('tr');
      const statusClass = it.status === 'success' ? 'badge-success' : 'badge-err';
      
      tr.innerHTML = `
        <td>${it.id}</td>
        <td>${it.file_name || '-'}</td>
        <td><span class="badge ${statusClass}">${it.status}</span></td>
        <td>${formatDate(it.created_at)}</td>
        <td>${it.inserted_rows || 0} / ${it.total_rows || 0}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--danger)">Error: ${err}</td></tr>`;
  }
}

// --- Initialization ---
async function checkDbAvailable() {
  try {
    await fetchJson('/api/ingests');
  } catch (err) {
    if (String(err).toLowerCase().includes('database unavailable')) {
      ['tab-uploads', 'tab-db'].forEach(id => {
        const b = el(id);
        if (b) { 
            b.disabled = true; 
            b.title = 'Database unavailable'; 
            b.style.opacity = '0.5';
        }
      });
      const list = el('uploads-list');
      if (list) list.innerHTML = '<div style="padding:1rem; color:var(--danger)">Database disconnected.</div>';
    }
  }
}

checkDbAvailable().finally(() => {
    // Determine default view
    showPanel('upload');
});