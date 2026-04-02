"""
工业缺陷类别预测系统 — Web 入口
使用 pywebview 创建桌面窗口，加载 Web 前端
"""

import os
import sys
from pathlib import Path

# PyInstaller 打包兼容
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    torch_lib_dir = os.path.join(base_dir, 'torch', 'lib')
    if os.path.isdir(torch_lib_dir):
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(torch_lib_dir)
        os.environ['PATH'] = torch_lib_dir + os.pathsep + os.environ.get('PATH', '')

import torch
_ = torch

import webview
from backend import Api

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    api = Api()
    html_path = Path(BASE_DIR, 'web', 'index.html').resolve().as_uri()

    window = webview.create_window(
        '工业缺陷类别预测系统',
        url=html_path,
        js_api=api,
        width=1500,
        height=980,
        min_size=(1100, 700),
        text_select=False,
    )
    api.set_window(window)

    webview.start(debug=False)


if __name__ == '__main__':
    main()
