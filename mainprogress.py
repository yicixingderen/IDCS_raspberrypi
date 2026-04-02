from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QBrush, QColor, QImage, QIcon
from PyQt5.QtWidgets import (QFileDialog, QApplication, QGraphicsDropShadowEffect,
                              QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame, QLabel,
                              QLineEdit, QPushButton, QSpacerItem)
from PyQt5.QtCore import Qt, QTimer

from datetime import datetime
import os
import numpy as np

from predict import predict_
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None


# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 全局变量
CAMERA_READ_FAIL_LIMIT = 10
CAMERA_SCAN_INDICES = (0, 1, 2, 3, 4, 5)

imgNamepath = ""

ALERT_THRESHOLD = 0.85
CAMERA_DEVICE_INDEX = 0
CAMERA_INTERVAL_MS = 900

# 全局样式表 - 浅色主题（与登录界面一致）
# 配色: #cccccc, #f0f0f0, #ffffff, #9DD6E0, 文字: #797979
LIGHT_STYLE = """
    QMainWindow {
        background-color: #ffffff;
    }
    QWidget#centralwidget {
        background: transparent;
    }
    QLabel#titleLabel {
        color: #797979;
        font-family: 'Microsoft YaHei UI', 'Segoe UI';
        font-size: 44px;
        font-weight: bold;
        background: transparent;
        letter-spacing: 4px;
    }
    QLabel#subtitleLabel {
        color: #9DD6E0;
        font-family: 'Consolas', 'Microsoft YaHei UI';
        font-size: 16px;
        letter-spacing: 4px;
        background: transparent;
    }
    QLabel#sectionLabel {
        color: #797979;
        font-family: 'Microsoft YaHei UI';
        font-size: 22px;
        font-weight: bold;
        background: transparent;
        letter-spacing: 2px;
    }
    QLabel#resultTitleLabel {
        color: #9DD6E0;
        font-family: 'Microsoft YaHei UI';
        font-size: 24px;
        font-weight: bold;
        letter-spacing: 4px;
        background: transparent;
    }
    QLabel#resultLabel {
        color: #797979;
        font-family: 'Microsoft YaHei UI';
        font-size: 22px;
        font-weight: bold;
        background: transparent;
    }
    QLabel#resultValue {
        color: #797979;
        font-family: 'Consolas', 'Microsoft YaHei UI';
        font-size: 24px;
        font-weight: bold;
        background: transparent;
    }
    QLabel#helpTitleLabel {
        color: #9DD6E0;
        font-family: 'Microsoft YaHei UI';
        font-size: 20px;
        font-weight: bold;
        background: transparent;
    }
    QLabel#helpTextLabel {
        color: #797979;
        font-family: 'Microsoft YaHei UI';
        font-size: 17px;
        background: transparent;
    }
    QLabel#statusLabel {
        color: #9DD6E0;
        font-family: 'Consolas', 'Microsoft YaHei UI';
        font-size: 17px;
        background: transparent;
    }
    QLineEdit {
        background-color: #ffffff;
        border: 2px solid #cccccc;
        border-radius: 12px;
        padding: 12px 18px;
        color: #797979;
        font-family: 'Microsoft YaHei UI';
        font-size: 17px;
        selection-background-color: #9DD6E0;
    }
    QLineEdit:focus {
        border: 2px solid #9DD6E0;
        background-color: #ffffff;
    }
    QPushButton#primaryBtn {
        background-color: #9DD6E0;
        border: none;
        border-radius: 14px;
        color: #ffffff;
        font-family: 'Droid Sans Fallback', 'Noto Sans CJK SC', 'Microsoft YaHei UI';
        font-size: 18px;
        font-weight: 600;
        padding: 12px 24px;
        min-width: 152px;
    }
    QPushButton#primaryBtn:hover {
        background-color: #8BC9D4;
    }
    QPushButton#primaryBtn:pressed {
        background-color: #7ABCC7;
    }
    QPushButton#secondaryBtn {
        background-color: #f0f0f0;
        border: 2px solid #cccccc;
        border-radius: 14px;
        color: #797979;
        font-family: 'Droid Sans Fallback', 'Noto Sans CJK SC', 'Microsoft YaHei UI';
        font-size: 18px;
        font-weight: 600;
        padding: 12px 24px;
        min-width: 152px;
    }
    QPushButton#secondaryBtn:hover {
        background-color: #ffffff;
        border: 2px solid #9DD6E0;
    }
    QPushButton#secondaryBtn:pressed {
        background-color: #f0f0f0;
        border: 2px solid #9DD6E0;
    }
    QFrame#toolbarFrame {
        background-color: #f0f0f0;
        border: 1px solid #cccccc;
        border-radius: 18px;
    }
    QFrame#imageFrame {
        background-color: #f0f0f0;
        border: 2px solid #cccccc;
        border-radius: 24px;
    }
    QFrame#resultFrame {
        background-color: #f0f0f0;
        border: 2px solid #9DD6E0;
        border-radius: 24px;
    }
    QFrame#resultCard {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 18px;
    }
    QFrame#helpCard {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 18px;
    }
    QFrame#imageDisplayFrame {
        background-color: #ffffff;
        border: 1px dashed #cccccc;
        border-radius: 18px;
    }
    QMenuBar {
        background-color: #f0f0f0;
        color: #797979;
        border-bottom: 1px solid #cccccc;
    }
    QStatusBar {
        background-color: #f0f0f0;
        color: #797979;
        border-top: 1px solid #cccccc;
    }
    QLabel#versionLabel {
        color: #cccccc;
        font-family: 'Consolas';
        font-size: 14px;
        background: transparent;
    }
"""


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        logo_path = os.path.join(BASE_DIR, 'logo.jpg')
        if os.path.exists(logo_path):
            MainWindow.setWindowIcon(QIcon(logo_path))
        
        # 增大默认窗口尺寸
        MainWindow.resize(1600, 1050)
        MainWindow.setMinimumSize(1300, 900)
        
        # 应用全局样式
        MainWindow.setStyleSheet(LIGHT_STYLE)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        # 主布局
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(40, 25, 40, 15)
        self.main_layout.setSpacing(15)
        
        # ========== 标题区域 ==========
        self.title_layout = QVBoxLayout()
        self.title_layout.setSpacing(5)
        
        self.label_2 = QLabel("工业缺陷类别预测系统")
        self.label_2.setObjectName("titleLabel")
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # 标题发光效果
        title_glow = QGraphicsDropShadowEffect()
        title_glow.setBlurRadius(15)
        title_glow.setColor(QColor(157, 214, 224, 100))
        title_glow.setOffset(0, 2)
        self.label_2.setGraphicsEffect(title_glow)
        self.title_layout.addWidget(self.label_2)
        
        self.subtitle_label = QLabel("INDUSTRIAL DEFECT CLASSIFICATION SYSTEM")
        self.subtitle_label.setObjectName("subtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.title_layout.addWidget(self.subtitle_label)
        
        self.main_layout.addLayout(self.title_layout)
        
        # ========== 工具栏区域 ==========
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("toolbarFrame")
        self.toolbar_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar_frame.setMinimumHeight(70)
        self.toolbar_frame.setMaximumHeight(80)
        
        self.toolbar_layout = QHBoxLayout(self.toolbar_frame)
        self.toolbar_layout.setContentsMargins(20, 12, 20, 12)
        self.toolbar_layout.setSpacing(14)
        
        # 选择图片按钮
        self.pushButton_2 = QPushButton("选择图片")
        self.pushButton_2.setObjectName("secondaryBtn")
        self.pushButton_2.setCursor(Qt.PointingHandCursor)
        self.pushButton_2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.pushButton_2.setMinimumWidth(176)
        self.toolbar_layout.addWidget(self.pushButton_2)
        
        # 路径输入框
        self.lineEdit_3 = QLineEdit()
        self.lineEdit_3.setPlaceholderText("请选择缺陷图片路径...")
        self.lineEdit_3.setReadOnly(True)
        self.lineEdit_3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar_layout.addWidget(self.lineEdit_3)
        
        # 开始预测按钮
        self.pushButton_3 = QPushButton("开始预测")
        self.pushButton_3.setObjectName("primaryBtn")
        self.pushButton_3.setCursor(Qt.PointingHandCursor)
        self.pushButton_3.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.pushButton_3.setMinimumWidth(176)
        self.toolbar_layout.addWidget(self.pushButton_3)

        # 开启摄像头按钮
        self.pushButton_camera_start = QPushButton("开启摄像头")
        self.pushButton_camera_start.setObjectName("secondaryBtn")
        self.pushButton_camera_start.setCursor(Qt.PointingHandCursor)
        self.pushButton_camera_start.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.pushButton_camera_start.setMinimumWidth(206)
        self.toolbar_layout.addWidget(self.pushButton_camera_start)

        # 关闭摄像头按钮
        self.pushButton_camera_stop = QPushButton("关闭摄像头")
        self.pushButton_camera_stop.setObjectName("secondaryBtn")
        self.pushButton_camera_stop.setCursor(Qt.PointingHandCursor)
        self.pushButton_camera_stop.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.pushButton_camera_stop.setMinimumWidth(206)
        self.toolbar_layout.addWidget(self.pushButton_camera_stop)
        
        self.main_layout.addWidget(self.toolbar_frame)
        
        # ========== 内容区域 ==========
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(25)
        
        # 左侧图片显示区域
        self.image_frame = QFrame()
        self.image_frame.setObjectName("imageFrame")
        self.image_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_frame.setMinimumSize(500, 500)
        
        self.image_layout = QVBoxLayout(self.image_frame)
        self.image_layout.setContentsMargins(20, 15, 20, 20)
        self.image_layout.setSpacing(10)
        
        # 图片区域标题
        self.label_5 = QLabel("[ 缺陷图像预览 ]")
        self.label_5.setObjectName("sectionLabel")
        self.label_5.setAlignment(Qt.AlignCenter)
        self.image_layout.addWidget(self.label_5)
        
        # 图片显示标签
        self.label_3 = QLabel()
        self.label_3.setObjectName("imageDisplayFrame")
        self.label_3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label_3.setAlignment(Qt.AlignCenter)
        self.label_3.setScaledContents(True)
        self.label_3.setMinimumSize(400, 400)
        self.image_layout.addWidget(self.label_3)
        
        self.content_layout.addWidget(self.image_frame, 3)
        
        # 右侧结果显示区域
        self.result_frame = QFrame()
        self.result_frame.setObjectName("resultFrame")
        self.result_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_frame.setMinimumWidth(380)
        self.result_frame.setMaximumWidth(500)
        
        self.result_layout = QVBoxLayout(self.result_frame)
        self.result_layout.setContentsMargins(20, 20, 20, 20)
        self.result_layout.setSpacing(20)
        
        # 结果区域标题
        self.result_title = QLabel("[ 预测结果 ]")
        self.result_title.setObjectName("resultTitleLabel")
        self.result_title.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(self.result_title)
        
        # 结果信息卡片
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.result_card.setMinimumHeight(200)
        
        self.result_card_layout = QVBoxLayout(self.result_card)
        self.result_card_layout.setContentsMargins(25, 25, 25, 25)
        self.result_card_layout.setSpacing(20)
        
        # 识别类别
        self.class_layout = QHBoxLayout()
        self.label_6 = QLabel("识别类别:")
        self.label_6.setObjectName("resultLabel")
        self.class_layout.addWidget(self.label_6)
        self.display_result = QLabel("--")
        self.display_result.setObjectName("resultValue")
        self.class_layout.addWidget(self.display_result)
        self.class_layout.addStretch()
        self.result_card_layout.addLayout(self.class_layout)
        
        # 识别准确率
        self.acc_layout = QHBoxLayout()
        self.label_7 = QLabel("识别准确率:")
        self.label_7.setObjectName("resultLabel")
        self.acc_layout.addWidget(self.label_7)
        self.disply_acc = QLabel("--")
        self.disply_acc.setObjectName("resultValue")
        self.acc_layout.addWidget(self.disply_acc)
        self.acc_layout.addStretch()
        self.result_card_layout.addLayout(self.acc_layout)
        
        # 状态指示器
        self.status_indicator = QLabel("等待选择图片...")
        self.status_indicator.setObjectName("statusLabel")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.result_card_layout.addWidget(self.status_indicator)
        
        self.result_layout.addWidget(self.result_card)
        
        # 使用说明区域
        self.help_frame = QFrame()
        self.help_frame.setObjectName("helpCard")
        self.help_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.help_layout = QVBoxLayout(self.help_frame)
        self.help_layout.setContentsMargins(20, 15, 20, 20)
        self.help_layout.setSpacing(10)
        
        self.help_title = QLabel("[ 使用说明 ]")
        self.help_title.setObjectName("helpTitleLabel")
        self.help_title.setAlignment(Qt.AlignCenter)
        self.help_layout.addWidget(self.help_title)
        
        self.help_text = QLabel(
            "1. 点击「选择图片」按钮进行单图预测\n"
            "2. 点击「开启摄像头」进行实时检测\n"
            "3. 异常阈值为 0.85，超过即输出异常日志\n"
            "4. 点击「关闭摄像头」停止实时检测"
        )
        self.help_text.setObjectName("helpTextLabel")
        self.help_text.setWordWrap(True)
        self.help_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.help_layout.addWidget(self.help_text)
        self.help_layout.addStretch()
        
        self.result_layout.addWidget(self.help_frame)
        
        self.content_layout.addWidget(self.result_frame, 2)
        
        self.main_layout.addLayout(self.content_layout, 1)
        
        # ========== 底部版本信息 ==========
        self.footer_layout = QHBoxLayout()
        
        self.deco_line1 = QFrame()
        self.deco_line1.setFixedHeight(2)
        self.deco_line1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.deco_line1.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #9DD6E0, stop:1 transparent);
        """)
        self.footer_layout.addWidget(self.deco_line1)
        
        self.version_label = QLabel("Version 1.0.1 | Powered by AI Technology")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.footer_layout.addWidget(self.version_label)
        
        self.deco_line2 = QFrame()
        self.deco_line2.setFixedHeight(2)
        self.deco_line2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.deco_line2.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:1 #9DD6E0);
        """)
        self.footer_layout.addWidget(self.deco_line2)
        
        self.main_layout.addLayout(self.footer_layout)
        
        # 隐藏原始 label (兼容性)
        self.label = QLabel()
        self.label.hide()

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.camera_timer = QTimer(self.centralwidget)
        self.camera_backend = None
        self.picam2 = None
        self.camera_timer.setInterval(CAMERA_INTERVAL_MS)
        self.camera_timer.timeout.connect(self.updateCameraFrame)
        self.camera_capture = None
        self.camera_active = False
        self.last_alert_print_at = None
        self.frame_read_failures = 0

        self.pushButton_2.clicked.connect(self.openImage)
        self.pushButton_3.clicked.connect(self.run)
        self.pushButton_camera_start.clicked.connect(self.startCamera)
        self.pushButton_camera_stop.clicked.connect(self.stopCamera)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "工业缺陷类别预测系统"))

    def openImage(self):
        global imgNamepath

        if self.camera_active:
            self.stopCamera()

        default_dir = os.path.join(BASE_DIR, 'data', 'test')
        if not os.path.exists(default_dir):
            default_dir = BASE_DIR
        imgNamepath, imgType = QFileDialog.getOpenFileName(
            self.centralwidget, "选择图片", default_dir,
            "*.jpg;;*.png;;All Files(*)"
        )
        if imgNamepath:
            pixmap = QtGui.QPixmap(imgNamepath)
            scaled_pixmap = pixmap.scaled(
                self.label_3.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label_3.setPixmap(scaled_pixmap)
            self.lineEdit_3.setText(imgNamepath)
            self._set_status("图片已加载，点击开始预测", "#5cb85c")

    def run(self):
        global imgNamepath

        if self.camera_active:
            self._set_status("摄像头检测中，请先关闭摄像头再进行单图预测", "#f0ad4e")
            return

        if not imgNamepath:
            self._set_status("请先选择图片！", "#d9534f")
            return

        self._set_status("正在预测中...", "#f0ad4e")
        QApplication.processEvents()

        file_name = str(imgNamepath)

        try:
            with Image.open(file_name) as opened_img:
                img = opened_img.convert('RGB')
            defect_type, confidence = predict_(img)
        except Exception as exc:
            self._set_status(f"预测失败: {exc}", "#d9534f")
            return

        self.display_result.setText(defect_type)
        self.disply_acc.setText(f"{float(confidence):.4f}")
        self._set_status("预测完成", "#5cb85c")
    def _set_status(self, text, color):
        self.status_indicator.setText(text)
        self.status_indicator.setStyleSheet(f"""
            color: {color};
            font-family: 'Consolas', 'Microsoft YaHei UI';
            font-size: 17px;
            background: transparent;
        """)

    def _probe_opencv_camera(self):
        if cv2 is None:
            return None, None

        ordered_indices = [CAMERA_DEVICE_INDEX]
        for idx in CAMERA_SCAN_INDICES:
            if idx not in ordered_indices:
                ordered_indices.append(idx)

        for camera_index in ordered_indices:
            for backend_name, backend_flag in (("V4L2", cv2.CAP_V4L2), ("DEFAULT", None)):
                capture = cv2.VideoCapture(camera_index, backend_flag) if backend_flag is not None else cv2.VideoCapture(camera_index)
                if not capture.isOpened():
                    capture.release()
                    continue

                capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                ready = False
                for _ in range(CAMERA_READ_FAIL_LIMIT):
                    ret, frame = capture.read()
                    if ret and frame is not None:
                        ready = True
                        break

                if ready:
                    return capture, f"OpenCV-{backend_name}(index={camera_index})"

                capture.release()

        return None, None

    def _probe_picamera2(self):
        if Picamera2 is None:
            return None

        picam2 = None
        try:
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            picam2.configure(config)
            picam2.start()

            for _ in range(CAMERA_READ_FAIL_LIMIT):
                frame = picam2.capture_array()
                if frame is not None:
                    return picam2

            picam2.stop()
            picam2.close()
            return None
        except Exception:
            if picam2 is not None:
                try:
                    picam2.stop()
                except Exception:
                    pass
                try:
                    picam2.close()
                except Exception:
                    pass
            return None

    def startCamera(self):
        global imgNamepath

        if self.camera_active:
            self._set_status("摄像头已开启，正在实时检测", "#5bc0de")
            return

        self.camera_capture = None
        self.picam2 = None
        self.camera_backend = None

        picam2 = self._probe_picamera2()
        if picam2 is not None:
            self.picam2 = picam2
            self.camera_backend = "Picamera2"
        else:
            capture, backend_desc = self._probe_opencv_camera()
            if capture is not None:
                self.camera_capture = capture
                self.camera_backend = backend_desc
            else:
                if cv2 is None and Picamera2 is None:
                    self._set_status("未安装 OpenCV/Picamera2，无法开启摄像头", "#d9534f")
                elif Picamera2 is None and cv2 is not None:
                    self._set_status("Picamera2 不可用，且 OpenCV 摄像头读取失败", "#d9534f")
                elif cv2 is None:
                    self._set_status("OpenCV 不可用，且 Picamera2 启动失败", "#d9534f")
                else:
                    self._set_status("摄像头打开失败，请检查连接或相机接口配置", "#d9534f")
                return

        self.camera_active = True
        self.last_alert_print_at = None
        self.frame_read_failures = 0
        imgNamepath = ""

        self.lineEdit_3.setText("实时摄像头输入中...")
        self.display_result.setText("--")
        self.disply_acc.setText("--")

        self.camera_timer.start()
        self._set_status(f"摄像头已开启({self.camera_backend})，正在实时预测", "#5bc0de")

    def stopCamera(self):
        if self.camera_timer.isActive():
            self.camera_timer.stop()

        if self.camera_capture is not None:
            self.camera_capture.release()
            self.camera_capture = None

        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass
            try:
                self.picam2.close()
            except Exception:
                pass
            self.picam2 = None

        self.camera_backend = None

        if self.camera_active:
            self.camera_active = False
            self.lineEdit_3.clear()
            self._set_status("摄像头已关闭", "#999999")

    def _read_camera_rgb_frame(self):
        if self.camera_capture is not None:
            ret, frame = self.camera_capture.read()
            if not ret or frame is None:
                return None
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.picam2 is not None:
            try:
                frame = self.picam2.capture_array()
            except Exception:
                return None

            if frame is None:
                return None

            if frame.ndim == 2:
                frame = np.stack((frame, frame, frame), axis=-1)
            elif frame.ndim == 3 and frame.shape[2] >= 3:
                frame = frame[:, :, :3]
            else:
                return None

            return np.ascontiguousarray(frame)

        return None

    def updateCameraFrame(self):
        if not self.camera_active:
            return

        rgb_frame = self._read_camera_rgb_frame()
        if rgb_frame is None:
            self.frame_read_failures += 1
            if self.frame_read_failures >= CAMERA_READ_FAIL_LIMIT:
                self._set_status("摄像头读取失败，请检查摄像头占用或分辨率", "#d9534f")
                self.stopCamera()
            else:
                self._set_status("摄像头预热中...", "#f0ad4e")
            return

        self.frame_read_failures = 0
        frame_height, frame_width, channel_count = rgb_frame.shape
        bytes_per_line = channel_count * frame_width
        frame_image = QImage(
            rgb_frame.data,
            frame_width,
            frame_height,
            bytes_per_line,
            QImage.Format_RGB888,
        )
        frame_pixmap = QPixmap.fromImage(frame_image)
        self.label_3.setPixmap(
            frame_pixmap.scaled(self.label_3.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

        try:
            result_type, confidence = predict_(Image.fromarray(rgb_frame))
        except Exception as exc:
            self._set_status(f"预测失败: {exc}", "#d9534f")
            return

        confidence = float(confidence)
        self.disply_acc.setText(f"{confidence:.4f}")

        if confidence > ALERT_THRESHOLD:
            self.display_result.setText(result_type)
            now = datetime.now()
            if self.last_alert_print_at is None or (now - self.last_alert_print_at).total_seconds() >= 1:
                print(
                    f"异常类型: {result_type} | 发生时间: {now.strftime('%Y-%m-%d %H:%M:%S')} | 准确率: {confidence:.4f}"
                )
                self.last_alert_print_at = now
            self._set_status(f"检测到异常: {result_type}", "#d9534f")
        else:
            self.display_result.setText("未检测到异常")
            self._set_status("未检测到异常", "#5cb85c")
            self.last_alert_print_at = None
    def closeEvent(self, event):
        self.stopCamera()
        event.accept()
