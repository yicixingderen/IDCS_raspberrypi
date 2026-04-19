/* ═══════════════════════════════════════════════════════════
   工业缺陷类别预测系统 — 前端逻辑
   ═══════════════════════════════════════════════════════════ */

const CATEGORIES = ['开裂', '内含物', '斑块', '点蚀表面', '轧制氧化皮', '划痕'];
const CAT_COLORS = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#38bdf8'];

let currentImagePath = null;
let batchImages = [];
let confirmCallback = null;

/* ─── Wait for pywebview API ─── */
function waitForApi() {
    return new Promise(resolve => {
        if (window.pywebview && window.pywebview.api) {
            resolve(window.pywebview.api);
        } else {
            window.addEventListener('pywebviewready', () => resolve(window.pywebview.api));
        }
    });
}

/* ─── Init ─── */
document.addEventListener('DOMContentLoaded', async () => {
    const api = await waitForApi();
    initLogin(api);
    initNav();
    initDetect(api);
    initBatch(api);
    initHistory(api);
    initCategories(api);
    initModal();
    initConfirm();
    initTags();
    loadDeviceInfo(api);
});

/* ═══════════ LOGIN ═══════════ */
function initLogin(api) {
    const screen = document.getElementById('login-screen');
    const btn = document.getElementById('login-btn');
    const userInput = document.getElementById('login-user');
    const passInput = document.getElementById('login-pass');
    const errorEl = document.getElementById('login-error');

    async function doLogin() {
        const u = userInput.value.trim();
        const p = passInput.value.trim();
        if (!u || !p) {
            errorEl.textContent = '请输入用户名和密码';
            return;
        }
        errorEl.textContent = '';
        const result = await api.login(u, p);
        if (result.success) {
            screen.classList.add('hidden');
            document.getElementById('app').classList.add('active');
            setTimeout(() => { screen.style.display = 'none'; }, 600);
            loadDashboard(api);
        } else {
            errorEl.textContent = result.message || '登录失败';
        }
    }

    btn.addEventListener('click', doLogin);
    passInput.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
    userInput.addEventListener('keydown', e => { if (e.key === 'Enter') passInput.focus(); });
}

/* ═══════════ NAVIGATION ═══════════ */
function initNav() {
    const items = document.querySelectorAll('.nav-item[data-page]');
    items.forEach(item => {
        item.addEventListener('click', () => {
            items.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            const page = document.getElementById('page-' + item.dataset.page);
            if (page) page.classList.add('active');
        });
    });
}

function navigateTo(pageName) {
    document.querySelectorAll('.nav-item[data-page]').forEach(i => {
        i.classList.toggle('active', i.dataset.page === pageName);
    });
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const page = document.getElementById('page-' + pageName);
    if (page) page.classList.add('active');
}

/* ═══════════ DASHBOARD ═══════════ */
async function loadDashboard(api) {
    const stats = await api.get_stats();
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-today').textContent = stats.today;
    const cs = stats.class_stats || {};
    const keys = Object.keys(cs);
    document.getElementById('stat-classes').textContent = keys.length;
    document.getElementById('stat-top').textContent = keys.length > 0
        ? keys.reduce((a, b) => cs[a] >= cs[b] ? a : b) : '—';

    drawPieChart(cs);
    loadRecentList(api);
    updateHistoryBadge(stats.total);
}

function updateHistoryBadge(count) {
    const badge = document.getElementById('nav-badge-history');
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = '';
    } else {
        badge.style.display = 'none';
    }
}

/* ─── Donut Chart (Canvas) ─── */
function drawPieChart(data) {
    const canvas = document.getElementById('chart-pie');
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    const w = rect.width - 40;
    const h = Math.min(w * 0.75, 320);
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    const entries = Object.entries(data);
    const total = entries.reduce((s, [, v]) => s + v, 0);
    if (total === 0) {
        ctx.fillStyle = '#64748b';
        ctx.font = `${Math.max(14, w * 0.04)}px "Microsoft YaHei UI"`;
        ctx.textAlign = 'center';
        ctx.fillText('暂无数据', w / 2, h / 2);
        return;
    }

    const cx = w * 0.35, cy = h / 2;
    const radius = Math.min(cx, cy) - 10;
    const inner = radius * 0.55;
    let startAngle = -Math.PI / 2;

    entries.forEach(([cls, count], i) => {
        const slice = (count / total) * Math.PI * 2;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, startAngle + slice);
        ctx.arc(cx, cy, inner, startAngle + slice, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = CAT_COLORS[CATEGORIES.indexOf(cls) % CAT_COLORS.length] || CAT_COLORS[i % CAT_COLORS.length];
        ctx.fill();
        startAngle += slice;
    });

    // Center text
    ctx.fillStyle = '#f1f5f9';
    ctx.font = `bold ${Math.max(18, w * 0.05)}px Consolas`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total, cx, cy - 8);
    ctx.fillStyle = '#64748b';
    ctx.font = `${Math.max(10, w * 0.028)}px "Microsoft YaHei UI"`;
    ctx.fillText('总计', cx, cy + 14);

    // Legend on the right
    const legendX = w * 0.65;
    const lineH = Math.max(22, h / (entries.length + 1));
    const legendStartY = (h - entries.length * lineH) / 2;
    const fontSize = Math.max(11, w * 0.03);

    entries.forEach(([cls, count], i) => {
        const y = legendStartY + i * lineH + lineH / 2;
        const color = CAT_COLORS[CATEGORIES.indexOf(cls) % CAT_COLORS.length] || CAT_COLORS[i % CAT_COLORS.length];
        ctx.fillStyle = color;
        ctx.fillRect(legendX, y - 5, 12, 12);
        ctx.fillStyle = '#f1f5f9';
        ctx.font = `${fontSize}px "Microsoft YaHei UI"`;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${cls}  ${count}`, legendX + 18, y + 1);
    });
}

async function loadRecentList(api) {
    const list = document.getElementById('recent-list');
    const records = await api.get_recent(8);
    if (!records || records.length === 0) {
        list.innerHTML = '<li class="empty-state"><div class="empty-icon">&#128269;</div>暂无记录</li>';
        return;
    }
    list.innerHTML = records.map(r => `
        <li>
            ${r.thumbnail ? `<img class="recent-thumb" src="${r.thumbnail}">` : '<span class="recent-thumb" style="background:var(--surface);display:inline-block;"></span>'}
            <span class="recent-class">${r.defect_class}</span>
            <span style="color:var(--accent);font-family:Consolas;font-size:var(--fs-xs)">${(r.confidence * 100).toFixed(1)}%</span>
            <span class="recent-time">${formatTime(r.created_at)}</span>
        </li>
    `).join('');
}

/* ═══════════ SINGLE DETECTION ═══════════ */
function initDetect(api) {
    const dropZone = document.getElementById('drop-zone');
    const btnSelect = document.getElementById('btn-select');
    const btnPredict = document.getElementById('btn-predict');

    btnSelect.addEventListener('click', async () => {
        const result = await api.select_image();
        if (result) loadDetectImage(result);
    });

    dropZone.addEventListener('click', async (e) => {
        if (dropZone.classList.contains('has-image')) return;
        const result = await api.select_image();
        if (result) loadDetectImage(result);
    });

    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', async e => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const path = files[0].path || files[0].name;
            if (/\.(jpe?g|png|bmp|tiff?)$/i.test(path)) {
                const b64 = await api.get_image_base64(path);
                if (b64) loadDetectImage({ path: path, name: files[0].name, base64: b64 });
            }
        }
    });

    btnPredict.addEventListener('click', async () => {
        if (!currentImagePath) {
            setDetectStatus('error', '请先选择图片');
            return;
        }
        setDetectStatus('analyzing', '正在分析中…');
        btnPredict.disabled = true;
        try {
            const result = await api.predict_single(currentImagePath);
            showDetectResult(result);
            loadDashboard(api);
        } catch (err) {
            setDetectStatus('error', '预测失败: ' + err);
        }
        btnPredict.disabled = false;
    });
}

function loadDetectImage(info) {
    currentImagePath = info.path;
    const img = document.getElementById('preview-img');
    const placeholder = document.getElementById('drop-placeholder');
    const zone = document.getElementById('drop-zone');
    img.src = info.base64;
    img.style.display = 'block';
    placeholder.style.display = 'none';
    zone.classList.add('has-image');
    setDetectStatus('waiting', '图片已加载 — ' + info.name);
}

function setDetectStatus(type, text) {
    const el = document.getElementById('detect-status');
    el.className = 'result-status ' + type;
    el.innerHTML = `<span class="dot"></span>${text}`;
}

function showDetectResult(result) {
    document.getElementById('result-class').textContent = result.class_name;
    const pct = (result.confidence * 100).toFixed(1);
    document.getElementById('result-conf').textContent = pct + '%';
    document.getElementById('conf-bar').style.width = pct + '%';
    document.getElementById('conf-text').textContent = pct + '%';
    setDetectStatus('done', '分析完成');
    highlightTag(result.class_name);
}

function initTags() {
    const grid = document.getElementById('tags-grid');
    grid.innerHTML = CATEGORIES.map(c => `<div class="tag" data-cat="${c}">${c}</div>`).join('');
}

function highlightTag(name) {
    document.querySelectorAll('#tags-grid .tag').forEach(t => {
        t.classList.toggle('active', t.dataset.cat === name);
    });
}

/* ═══════════ BATCH DETECTION ═══════════ */
function initBatch(api) {
    const btnSelect = document.getElementById('btn-batch-select');
    const btnRun = document.getElementById('btn-batch-run');
    const progress = document.getElementById('batch-progress');

    btnSelect.addEventListener('click', async () => {
        const result = await api.select_images();
        if (result && result.length > 0) {
            batchImages = result;
            renderBatchPreview();
            btnRun.disabled = false;
            progress.textContent = `已选择 ${result.length} 张图片`;
        }
    });

    btnRun.addEventListener('click', async () => {
        if (batchImages.length === 0) return;
        btnRun.disabled = true;
        btnSelect.disabled = true;
        const paths = batchImages.map(img => img.path);
        const total = paths.length;

        // Process one by one for progress
        for (let i = 0; i < total; i++) {
            progress.textContent = `正在识别 ${i + 1} / ${total}...`;
            try {
                const result = await api.predict_single(paths[i]);
                updateBatchRow(i, result);
            } catch (err) {
                updateBatchRow(i, { success: false, error: String(err) });
            }
        }

        progress.textContent = `完成！共 ${total} 张`;
        btnSelect.disabled = false;
        btnRun.disabled = false;
        loadDashboard(api);
    });
}

function renderBatchPreview() {
    const tbody = document.getElementById('batch-tbody');
    const empty = document.getElementById('batch-empty');
    empty.style.display = 'none';
    document.getElementById('batch-table').style.display = '';
    tbody.innerHTML = batchImages.map((img, i) => `
        <tr id="batch-row-${i}">
            <td class="thumb-cell"><img src="${img.base64}" alt=""></td>
            <td>${img.name}</td>
            <td class="batch-class">—</td>
            <td class="batch-conf">—</td>
            <td class="batch-status" style="color:var(--text-muted)">等待中</td>
        </tr>
    `).join('');
}

function updateBatchRow(index, result) {
    const row = document.getElementById('batch-row-' + index);
    if (!row) return;
    if (result.class_name) {
        row.querySelector('.batch-class').textContent = result.class_name;
        row.querySelector('.batch-conf').textContent = (result.confidence * 100).toFixed(1) + '%';
        row.querySelector('.batch-status').textContent = '完成';
        row.querySelector('.batch-status').style.color = 'var(--success)';
    } else {
        row.querySelector('.batch-status').textContent = '失败';
        row.querySelector('.batch-status').style.color = 'var(--error)';
    }
}

/* ═══════════ HISTORY ═══════════ */
function initHistory(api) {
    const searchInput = document.getElementById('history-search');
    let searchTimeout = null;

    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadHistory(api, searchInput.value.trim()), 300);
    });

    document.getElementById('btn-export').addEventListener('click', async () => {
        const result = await api.export_csv();
        if (result && result.success) {
            setDetectStatus('done', 'CSV 已导出');
        }
    });

    document.getElementById('btn-clear-all').addEventListener('click', () => {
        showConfirm('确定要清空所有历史记录吗？此操作不可撤销。', async () => {
            await api.clear_history();
            loadHistory(api);
            loadDashboard(api);
        });
    });

    // Auto-load when navigating to history
    const observer = new MutationObserver(() => {
        if (document.getElementById('page-history').classList.contains('active')) {
            loadHistory(api, searchInput.value.trim());
        }
    });
    observer.observe(document.getElementById('page-history'), { attributes: true, attributeFilter: ['class'] });
}

async function loadHistory(api, keyword) {
    let records;
    if (keyword) {
        records = await api.search_history(keyword);
    } else {
        records = await api.get_history();
    }

    const tbody = document.getElementById('history-tbody');
    const empty = document.getElementById('history-empty');

    if (!records || records.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';

    tbody.innerHTML = records.map(r => `
        <tr>
            <td class="thumb-cell">
                ${r.thumbnail ? `<img src="${r.thumbnail}" alt="" style="cursor:pointer" onclick="previewRecord(${r.id}, '${escPath(r.image_path)}', '${escHtml(r.defect_class)}', ${r.confidence}, '${escHtml(r.created_at)}')">` : '—'}
            </td>
            <td>${escHtml(r.image_name)}</td>
            <td>${escHtml(r.defect_class)}</td>
            <td style="font-family:Consolas;color:var(--accent)">${(r.confidence * 100).toFixed(1)}%</td>
            <td style="font-family:Consolas;font-size:var(--fs-xs);color:var(--text-muted)">${formatTime(r.created_at)}</td>
            <td class="table-actions">
                <button onclick="loadToDetect('${escPath(r.image_path)}')">识别</button>
                <button class="delete-btn" onclick="deleteRecord(${r.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

// Global functions for inline handlers
window._api = null;
waitForApi().then(api => { window._api = api; });

window.deleteRecord = async function(id) {
    if (!window._api) return;
    await window._api.delete_record(id);
    const keyword = document.getElementById('history-search').value.trim();
    loadHistory(window._api, keyword);
    loadDashboard(window._api);
};

window.loadToDetect = async function(path) {
    if (!window._api) return;
    const b64 = await window._api.get_image_base64(path);
    if (b64) {
        loadDetectImage({ path: path, name: path.split(/[\\/]/).pop(), base64: b64 });
        navigateTo('detect');
    }
};

window.previewRecord = async function(id, path, cls, conf, time) {
    if (!window._api) return;
    let src = await window._api.get_image_base64(path);
    if (!src) {
        // Fallback: get full thumbnail from history
        const records = await window._api.get_history();
        const rec = records.find(r => r.id === id);
        if (rec && rec.thumbnail) src = rec.thumbnail;
    }
    if (src) {
        showPreviewModal(src, cls, conf, time);
    }
};

/* ═══════════ CATEGORIES ═══════════ */
function initCategories(api) {
    const observer = new MutationObserver(() => {
        if (document.getElementById('page-categories').classList.contains('active')) {
            loadCategories(api);
        }
    });
    observer.observe(document.getElementById('page-categories'), { attributes: true, attributeFilter: ['class'] });
}

async function loadCategories(api) {
    const stats = await api.get_stats();
    const cs = stats.class_stats || {};
    const total = Object.values(cs).reduce((a, b) => a + b, 0);
    const list = document.getElementById('cat-list');

    list.innerHTML = `<div class="cat-list-item active" data-cat="__all__">
            <span>全部</span><span class="cat-count">${total}</span>
        </div>` +
        CATEGORIES.map(c => `<div class="cat-list-item" data-cat="${c}">
            <span>${c}</span><span class="cat-count">${cs[c] || 0}</span>
        </div>`).join('');

    list.querySelectorAll('.cat-list-item').forEach(item => {
        item.addEventListener('click', async () => {
            list.querySelectorAll('.cat-list-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            const cat = item.dataset.cat;
            let records;
            if (cat === '__all__') {
                records = await api.get_history();
                document.getElementById('cat-title').textContent = `ALL IMAGES (${records.length})`;
            } else {
                records = await api.get_history_by_class(cat);
                document.getElementById('cat-title').textContent = `${cat} (${records.length})`;
            }
            renderCatGrid(records);
        });
    });

    // Load "all" by default
    let all = await api.get_history();
    document.getElementById('cat-title').textContent = `ALL IMAGES (${all.length})`;
    renderCatGrid(all);
}

function renderCatGrid(records) {
    const grid = document.getElementById('cat-grid');
    if (!records || records.length === 0) {
        grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><div class="empty-icon">&#128247;</div><p>此类别暂无图片</p></div>';
        return;
    }
    grid.innerHTML = records.map(r => `
        <div class="thumb-card" onclick="previewRecord(${r.id}, '${escPath(r.image_path)}', '${escHtml(r.defect_class)}', ${r.confidence}, '${escHtml(r.created_at)}')">
            ${r.thumbnail ? `<img src="${r.thumbnail}" alt="">` : '<div style="aspect-ratio:1;background:var(--surface);"></div>'}
            <div class="thumb-info">
                <div class="thumb-name">${escHtml(r.image_name)}</div>
                <div class="thumb-conf">${(r.confidence * 100).toFixed(1)}%</div>
            </div>
        </div>
    `).join('');
}

/* ═══════════ MODAL / PREVIEW ═══════════ */
function initModal() {
    const overlay = document.getElementById('modal-preview');
    document.getElementById('modal-close').addEventListener('click', () => overlay.classList.remove('active'));
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('active'); });
}

function showPreviewModal(imgSrc, cls, conf, time) {
    document.getElementById('modal-img').src = imgSrc;
    document.getElementById('modal-info').innerHTML = `
        <div class="modal-info-item"><span class="label">缺陷类别</span><span class="value">${cls}</span></div>
        <div class="modal-info-item"><span class="label">置信度</span><span class="value" style="color:var(--accent)">${(conf * 100).toFixed(1)}%</span></div>
        <div class="modal-info-item"><span class="label">识别时间</span><span class="value" style="font-size:var(--fs-sm)">${time}</span></div>
    `;
    document.getElementById('modal-preview').classList.add('active');
}

/* ═══════════ CONFIRM DIALOG ═══════════ */
function initConfirm() {
    document.getElementById('confirm-no').addEventListener('click', () => {
        document.getElementById('confirm-overlay').classList.remove('active');
        confirmCallback = null;
    });
    document.getElementById('confirm-yes').addEventListener('click', () => {
        document.getElementById('confirm-overlay').classList.remove('active');
        if (confirmCallback) { confirmCallback(); confirmCallback = null; }
    });
}

function showConfirm(msg, callback) {
    document.getElementById('confirm-msg').textContent = msg;
    confirmCallback = callback;
    document.getElementById('confirm-overlay').classList.add('active');
}

/* ═══════════ DEVICE INFO ═══════════ */
async function loadDeviceInfo(api) {
    const info = await api.get_device_info();
    document.getElementById('device-info').innerHTML =
        `Device: ${info.device}<br>Model: ${info.model}<br>v2.0.0`;
}

/* ═══════════ UTILS ═══════════ */
function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function escPath(str) {
    // For use in onclick attributes — double-escape backslashes
    if (!str) return '';
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function formatTime(ts) {
    if (!ts) return '';
    // Already formatted from SQLite
    return ts.replace('T', ' ').substring(0, 19);
}

/* Redraw chart on resize */
let resizeTimer = null;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(async () => {
        if (document.getElementById('page-dashboard').classList.contains('active') && window._api) {
            const stats = await window._api.get_stats();
            drawPieChart(stats.class_stats || {});
        }
    }, 200);
});
