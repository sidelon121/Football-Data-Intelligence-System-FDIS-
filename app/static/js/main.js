/**
 * FDIS — Football Data Intelligence System
 * Core JavaScript
 */

// ─── Toast Notifications ─────────────────────────────────────────
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── Plotly Chart Rendering ──────────────────────────────────────
function renderChart(elementId, chartData) {
    if (!chartData || !document.getElementById(elementId)) return;
    
    const config = {
        responsive: true,
        displayModeBar: false,
        scrollZoom: false,
    };

    try {
        Plotly.newPlot(elementId, chartData.data, chartData.layout, config);
    } catch (e) {
        console.error(`Failed to render chart ${elementId}:`, e);
    }
}

// ─── File Upload Handler ─────────────────────────────────────────
function initUpload() {
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');

    if (!zone) return;

    // Click to select
    zone.addEventListener('click', () => fileInput.click());

    // Drag and drop
    ['dragenter', 'dragover'].forEach(event => {
        zone.addEventListener(event, (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        zone.addEventListener(event, (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
        });
    });

    zone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    const zone = document.getElementById('upload-zone');
    const fileInfo = document.getElementById('file-info');
    const uploadBtn = document.getElementById('upload-btn');

    if (zone) {
        zone.innerHTML = `
            <div class="upload-icon">📄</div>
            <h3>${file.name}</h3>
            <p>${(file.size / 1024).toFixed(1)} KB — Ready to upload</p>
        `;
    }
    if (uploadBtn) {
        uploadBtn.classList.remove('hidden');
    }
}

function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const dataType = document.getElementById('data-type');
    const progressBar = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');

    if (!fileInput.files.length) {
        showToast('Please select a file first', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    if (dataType) {
        formData.append('data_type', dataType.value);
    }

    if (progressBar) progressBar.classList.remove('hidden');

    fetch('/api/upload', {
        method: 'POST',
        body: formData,
    })
    .then(res => res.json())
    .then(data => {
        if (progressFill) progressFill.style.width = '100%';
        
        if (data.success) {
            showToast(data.message || 'Upload successful!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(data.error || 'Upload failed', 'error');
        }
    })
    .catch(err => {
        showToast('Upload failed: ' + err.message, 'error');
    })
    .finally(() => {
        if (progressFill) {
            setTimeout(() => {
                if (progressBar) progressBar.classList.add('hidden');
                progressFill.style.width = '0%';
            }, 2000);
        }
    });
}

// ─── Manual Entry Form ───────────────────────────────────────────
function submitManualEntry() {
    const form = document.getElementById('manual-entry-form');
    if (!form) return;

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    fetch('/api/manual-entry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            showToast('Match data saved successfully!', 'success');
            form.reset();
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(result.errors?.join(', ') || 'Failed to save', 'error');
        }
    })
    .catch(err => showToast('Error: ' + err.message, 'error'));
}

// ─── Comparison Tool ─────────────────────────────────────────────
function loadComparison() {
    const type = document.getElementById('compare-type')?.value || 'team';
    const id1 = document.getElementById('compare-id1')?.value;
    const id2 = document.getElementById('compare-id2')?.value;

    if (!id1 || !id2) {
        showToast('Please select both items to compare', 'warning');
        return;
    }

    if (id1 === id2) {
        showToast('Please select two different items', 'warning');
        return;
    }

    const resultDiv = document.getElementById('comparison-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="flex-center" style="padding:40px"><div class="spinner"></div></div>';
    }

    fetch(`/api/compare?type=${type}&id1=${id1}&id2=${id2}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            displayComparison(data, type);
        })
        .catch(err => showToast('Comparison failed: ' + err.message, 'error'));
}

function displayComparison(data, type) {
    const resultDiv = document.getElementById('comparison-result');
    if (!resultDiv) return;

    if (type === 'team') {
        const t1 = data.comparison.team1;
        const t2 = data.comparison.team2;
        const h2h = data.comparison.head_to_head;

        let html = `
            <div class="card mb-3">
                <div class="scoreboard">
                    <div class="team-name">${t1.team.name}</div>
                    <div>
                        <div class="score">${t1.points} <span class="score-separator">vs</span> ${t2.points}</div>
                        <div class="text-muted text-center" style="font-size:0.8rem">POINTS</div>
                    </div>
                    <div class="team-name">${t2.team.name}</div>
                </div>
            </div>
            <div class="grid-2 mb-3">
                <div class="card">
                    <h4 style="margin-bottom:12px">${t1.team.name}</h4>
                    <div class="stat-row"><span class="text-muted">Record:</span> ${t1.wins}W ${t1.draws}D ${t1.losses}L</div>
                    <div class="stat-row"><span class="text-muted">Win Rate:</span> ${t1.win_rate}%</div>
                    <div class="stat-row"><span class="text-muted">Goals:</span> ${t1.goals_for} scored, ${t1.goals_against} conceded</div>
                    <div class="stat-row"><span class="text-muted">Possession:</span> ${t1.avg_possession}%</div>
                    <div class="stat-row"><span class="text-muted">xG:</span> ${t1.avg_xg}</div>
                </div>
                <div class="card">
                    <h4 style="margin-bottom:12px">${t2.team.name}</h4>
                    <div class="stat-row"><span class="text-muted">Record:</span> ${t2.wins}W ${t2.draws}D ${t2.losses}L</div>
                    <div class="stat-row"><span class="text-muted">Win Rate:</span> ${t2.win_rate}%</div>
                    <div class="stat-row"><span class="text-muted">Goals:</span> ${t2.goals_for} scored, ${t2.goals_against} conceded</div>
                    <div class="stat-row"><span class="text-muted">Possession:</span> ${t2.avg_possession}%</div>
                    <div class="stat-row"><span class="text-muted">xG:</span> ${t2.avg_xg}</div>
                </div>
            </div>`;

        // Chart
        html += `<div class="card mb-3"><div id="comparison-chart" class="chart-container"></div></div>`;

        // Narrative
        if (data.narrative) {
            html += `<div class="card"><div class="card-header"><span class="card-title">📝 Analysis</span></div><div class="analysis-text">${markdownToHtml(data.narrative)}</div></div>`;
        }

        resultDiv.innerHTML = html;

        // Render chart
        if (data.chart) {
            renderChart('comparison-chart', data.chart);
        }
    }
}

// ─── Tab Navigation ──────────────────────────────────────────────
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const group = tab.closest('.tabs');
            const targetId = tab.dataset.tab;

            group.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            document.querySelectorAll('.tab-content').forEach(tc => {
                tc.classList.remove('active');
            });
            const target = document.getElementById(targetId);
            if (target) target.classList.add('active');
        });
    });
}

// ─── Mobile Sidebar Toggle ───────────────────────────────────────
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('open');
}

// ─── Markdown to HTML (basic) ────────────────────────────────────
function markdownToHtml(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>');
}

// ─── Fetch API with loading state ────────────────────────────────
async function fetchWithLoading(url, elementId) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = '<div class="flex-center" style="padding:40px"><div class="spinner"></div></div>';
    
    try {
        const res = await fetch(url);
        return await res.json();
    } catch (err) {
        if (el) el.innerHTML = `<div class="empty-state"><p>Failed to load data</p></div>`;
        throw err;
    }
}

// ─── Team Selector for Dashboard ─────────────────────────────────
function onTeamSelect(selectElement) {
    const teamId = selectElement.value;
    if (!teamId) return;
    window.location.href = `/teams/${teamId}`;
}

// ─── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUpload();

    // Render any charts passed as data attributes
    document.querySelectorAll('[data-chart]').forEach(el => {
        try {
            const chartData = JSON.parse(el.dataset.chart);
            renderChart(el.id, chartData);
        } catch (e) {
            console.error('Failed to parse chart data for', el.id, e);
        }
    });
});
