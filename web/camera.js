/* 摄像头实时检测逻辑（Web版） */

const CAMERA_POLL_MS = 900;

let cameraTimer = null;
let cameraRunning = false;
let cameraBusy = false;

function updateCameraButtons() {
    const startBtn = document.getElementById('btn-camera-start');
    const stopBtn = document.getElementById('btn-camera-stop');
    if (!startBtn || !stopBtn) return;
    startBtn.disabled = cameraRunning;
    stopBtn.disabled = !cameraRunning;
}

function clearTagHighlight() {
    document.querySelectorAll('#tags-grid .tag').forEach(t => t.classList.remove('active'));
}

function renderCameraResult(result) {
    const img = document.getElementById('preview-img');
    const placeholder = document.getElementById('drop-placeholder');
    const zone = document.getElementById('drop-zone');

    if (result.frame_base64) {
        img.src = result.frame_base64;
        img.style.display = 'block';
        placeholder.style.display = 'none';
        zone.classList.add('has-image');
    }

    const pct = (Number(result.confidence || 0) * 100).toFixed(1);
    document.getElementById('result-class').textContent = result.display_class || '—';
    document.getElementById('result-conf').textContent = pct + '%';
    document.getElementById('conf-bar').style.width = pct + '%';
    document.getElementById('conf-text').textContent = pct + '%';

    if (result.alert) {
        if (typeof highlightTag === 'function') {
            highlightTag(result.class_name);
        }
        setDetectStatus('error', result.status || `检测到异常: ${result.class_name}`);
    } else {
        clearTagHighlight();
        setDetectStatus('done', result.status || '未检测到异常');
    }
}

async function pollCameraFrame(api) {
    if (!cameraRunning || cameraBusy) return;

    cameraBusy = true;
    try {
        const result = await api.get_camera_frame();
        if (!result || !result.success) {
            if (result && result.stopped) {
                await stopCamera(api, true);
                setDetectStatus('error', result.message || '摄像头读取失败');
            } else if (result && result.message) {
                setDetectStatus('analyzing', result.message);
            }
            return;
        }
        renderCameraResult(result);
    } catch (err) {
        setDetectStatus('error', '摄像头读取失败: ' + err);
    } finally {
        cameraBusy = false;
    }
}

async function startCamera(api) {
    if (cameraRunning) return;

    setDetectStatus('analyzing', '正在启动摄像头...');
    const result = await api.start_camera();
    if (!result || !result.success) {
        setDetectStatus('error', (result && result.message) || '摄像头打开失败');
        return;
    }

    cameraRunning = true;
    cameraBusy = false;
    updateCameraButtons();
    setDetectStatus('analyzing', result.message || '摄像头已开启');

    await pollCameraFrame(api);
    cameraTimer = setInterval(() => {
        pollCameraFrame(api);
    }, CAMERA_POLL_MS);
}

async function stopCamera(api, silent) {
    if (cameraTimer) {
        clearInterval(cameraTimer);
        cameraTimer = null;
    }

    cameraRunning = false;
    cameraBusy = false;
    updateCameraButtons();

    try {
        const result = await api.stop_camera();
        if (!silent) {
            setDetectStatus('waiting', (result && result.message) || '摄像头已关闭');
        }
    } catch (err) {
        if (!silent) {
            setDetectStatus('error', '关闭摄像头失败: ' + err);
        }
    }
}

function bindCameraActions(api) {
    const startBtn = document.getElementById('btn-camera-start');
    const stopBtn = document.getElementById('btn-camera-stop');
    const predictBtn = document.getElementById('btn-predict');
    const selectBtn = document.getElementById('btn-select');
    const detectPage = document.getElementById('page-detect');

    if (!startBtn || !stopBtn || !detectPage) return;

    startBtn.addEventListener('click', () => startCamera(api));
    stopBtn.addEventListener('click', () => stopCamera(api, false));

    if (predictBtn) {
        predictBtn.addEventListener('click', (e) => {
            if (!cameraRunning) return;
            e.preventDefault();
            e.stopImmediatePropagation();
            setDetectStatus('error', '请先关闭摄像头，再进行图片预测');
        }, true);
    }

    if (selectBtn) {
        selectBtn.addEventListener('click', async () => {
            if (cameraRunning) {
                await stopCamera(api, true);
            }
        }, true);
    }

    const observer = new MutationObserver(async () => {
        if (!detectPage.classList.contains('active') && cameraRunning) {
            await stopCamera(api, true);
        }
    });
    observer.observe(detectPage, { attributes: true, attributeFilter: ['class'] });

    window.addEventListener('beforeunload', () => {
        if (cameraRunning) {
            api.stop_camera();
        }
    });

    updateCameraButtons();
}

document.addEventListener('DOMContentLoaded', async () => {
    const api = await waitForApi();
    bindCameraActions(api);
});
