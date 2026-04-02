#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

sudo apt update
sudo apt install -y \
  python3-venv \
  python3-pyqt5 \
  python3-pil \
  python3-torch \
  python3-torchvision \
  python3-opencv \
  python3-picamera2 \
  python3-gi \
  python3-gi-cairo \
  libgtk-3-0

if apt-cache show gir1.2-webkit2-4.1 >/dev/null 2>&1; then
  sudo apt install -y gir1.2-webkit2-4.1
else
  sudo apt install -y gir1.2-webkit2-4.0
fi

python3 -m venv .venv --system-site-packages
. .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -U pywebview

python -c "import PyQt5, torch, torchvision, PIL, cv2, webview; print('IDCS_rasp environment ready')"
