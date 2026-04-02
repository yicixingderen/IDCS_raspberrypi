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

# 桌面版（PyQt）入口；若需Web版请运行 ./run_web.sh
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"

echo "[IDCS] Launching Desktop edition (PyQt). For Web edition run: ./run_web.sh"
python enterLogin.py
