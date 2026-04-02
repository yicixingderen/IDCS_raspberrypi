#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv. Run ./setup_debian.sh first."
  exit 1
fi

. .venv/bin/activate

if [[ -z "${DISPLAY:-}" && -S /tmp/.X11-unix/X0 ]]; then
  export DISPLAY=:0
fi

if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "/run/user/$(id -u)" ]]; then
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
fi

# Raspberry Pi 上 WebKit 合成有时会导致花屏，默认走软件渲染。
export PYWEBVIEW_GUI="${PYWEBVIEW_GUI:-gtk}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export WEBKIT_DISABLE_COMPOSITING_MODE="${WEBKIT_DISABLE_COMPOSITING_MODE:-1}"
export WEBKIT_DISABLE_DMABUF_RENDERER="${WEBKIT_DISABLE_DMABUF_RENDERER:-1}"

echo "[IDCS] Launching Web edition (pywebview)..."
python app.py
