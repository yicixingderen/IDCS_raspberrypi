import os
import sys


def _configure_frozen_torch_runtime():
    """Handle runtime library paths for packaged builds."""
    if not getattr(sys, 'frozen', False):
        return

    base_dir = sys._MEIPASS
    torch_lib_dir = os.path.join(base_dir, 'torch', 'lib')
    if not os.path.isdir(torch_lib_dir):
        return

    # Windows needs add_dll_directory for packaged torch runtime.
    if os.name == 'nt' and hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(torch_lib_dir)

    os.environ['PATH'] = torch_lib_dir + os.pathsep + os.environ.get('PATH', '')


def _configure_linux_gui_env():
    """Provide sane defaults when launched from tty or VS Code remote terminals."""
    if not sys.platform.startswith('linux'):
        return

    if not os.environ.get('DISPLAY') and os.path.exists('/tmp/.X11-unix/X0'):
        os.environ['DISPLAY'] = ':0'

    if not os.environ.get('XDG_RUNTIME_DIR'):
        candidate_runtime_dir = f"/run/user/{os.getuid()}"
        if os.path.isdir(candidate_runtime_dir):
            os.environ['XDG_RUNTIME_DIR'] = candidate_runtime_dir


def _configure_qt_plugin_path():
    import PyQt5

    qt_plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
    if os.path.isdir(qt_plugin_path):
        os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', qt_plugin_path)


_configure_frozen_torch_runtime()
_configure_linux_gui_env()

# Import torch before PyQt to reduce packaged runtime conflicts.
import torch
_ = torch

_configure_qt_plugin_path()

import enterMainprogress
import login
from PyQt5.QtWidgets import QApplication, QMainWindow


class FirstWindowActions(login.Ui_MainWindow, QMainWindow):

    def __init__(self):
        super(FirstWindowActions, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.click_login_button)

    def click_login_button(self):
        self.scend_window = enterMainprogress.SecondWindowActions()
        self.scend_window.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = FirstWindowActions()
    MainWindow.show()

    sys.exit(app.exec_())
