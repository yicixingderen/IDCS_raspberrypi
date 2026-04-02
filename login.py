from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QPixmap, QBrush, QLinearGradient, QColor, QPainter
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (QGraphicsDropShadowEffect, QVBoxLayout, QHBoxLayout, 
                              QSpacerItem, QSizePolicy, QFrame, QLabel, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 全局样式表 - 浅色主题
# 配色: #cccccc, #f0f0f0, #ffffff, #9DD6E0, 文字: #797979
LIGHT_STYLE = """
    QMainWindow {
        background-color: #ffffff;
    }
    QWidget#centralwidget {
        background: transparent;
    }
    QWidget#backgroundWidget {
        background: transparent;
    }
    QLabel#titleLabel {
        color: #3a3a3a;
        font-family: 'Microsoft YaHei UI', 'Segoe UI';
        font-size: 52px;
        font-weight: bold;
        background: transparent;
    }
    QLabel#subtitleLabel {
        color: #9DD6E0;
        font-family: 'Consolas', 'Microsoft YaHei UI';
        font-size: 22px;
        font-weight: bold;
        letter-spacing: 4px;
        background: transparent;
    }
    QLabel#fieldLabel {
        color: #797979;
        font-family: 'Microsoft YaHei UI', 'Segoe UI';
        font-size: 22px;
        font-weight: 500;
        background: transparent;
    }
    QLabel#loginTitleLabel {
        color: #797979;
        font-family: 'Microsoft YaHei UI';
        font-size: 34px;
        font-weight: bold;
        letter-spacing: 4px;
        background: transparent;
    }
    QLineEdit {
        background-color: #ffffff;
        border: 2px solid #cccccc;
        border-radius: 14px;
        padding: 18px 24px;
        color: #797979;
        font-family: 'Microsoft YaHei UI';
        font-size: 20px;
        selection-background-color: #9DD6E0;
        min-height: 32px;
    }
    QLineEdit:focus {
        border: 2px solid #9DD6E0;
        background-color: #ffffff;
    }
    QLineEdit:hover {
        border: 2px solid #9DD6E0;
        background-color: #f0f0f0;
    }
    QPushButton#loginBtn {
        background-color: #9DD6E0;
        border: none;
        border-radius: 28px;
        color: #ffffff;
        font-family: 'Microsoft YaHei UI', 'Segoe UI';
        font-size: 24px;
        font-weight: bold;
        padding: 22px 70px;
        letter-spacing: 6px;
        min-height: 36px;
    }
    QPushButton#loginBtn:hover {
        background-color: #8BC9D4;
    }
    QPushButton#loginBtn:pressed {
        background-color: #7ABCC7;
    }
    QFrame#loginFrame {
        background-color: rgba(255, 255, 255, 0.92);
        border: 2px solid rgba(157, 214, 224, 0.6);
        border-radius: 30px;
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
        color: #9DD6E0;
        font-family: 'Consolas';
        font-size: 14px;
        font-weight: bold;
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
        MainWindow.resize(1500, 1000)
        MainWindow.setMinimumSize(1100, 800)
        
        # 应用全局样式
        MainWindow.setStyleSheet(LIGHT_STYLE)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        # 设置背景图片
        self.background_label = QLabel(self.centralwidget)
        self.background_label.setObjectName("backgroundWidget")
        bg_path = os.path.join(BASE_DIR, 'login_background.jpg')
        if os.path.exists(bg_path):
            self.background_pixmap = QPixmap(bg_path)
        else:
            # 如果没有背景图，创建纯色背景
            self.background_pixmap = QPixmap(1500, 1000)
            self.background_pixmap.fill(QColor(240, 240, 240))
        
        # 主布局
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(50, 30, 50, 20)
        self.main_layout.setSpacing(15)
        
        # ========== 标题区域 ==========
        self.title_layout = QVBoxLayout()
        self.title_layout.setSpacing(8)
        
        self.label = QLabel()
        self.label.setObjectName("titleLabel")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.label.setMinimumHeight(60)
        # 添加发光效果
        title_glow = QGraphicsDropShadowEffect()
        title_glow.setBlurRadius(20)
        title_glow.setColor(QColor(157, 214, 224, 100))
        title_glow.setOffset(0, 2)
        self.label.setGraphicsEffect(title_glow)
        self.title_layout.addWidget(self.label)
        
        self.subtitle_label = QLabel("INDUSTRIAL DEFECT CLASSIFICATION SYSTEM")
        self.subtitle_label.setObjectName("subtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_layout.addWidget(self.subtitle_label)
        
        self.main_layout.addLayout(self.title_layout)
        
        # ========== 内容区域 ==========
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(40)
        
        self.content_layout.addStretch(1)  # 左侧弹性空间
        
        # 中间登录框
        self.login_frame = QFrame()
        self.login_frame.setObjectName("loginFrame")
        self.login_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.login_frame.setMinimumSize(380, 420)
        self.login_frame.setMaximumWidth(550)
        
        self.login_layout = QVBoxLayout(self.login_frame)
        self.login_layout.setContentsMargins(50, 40, 50, 40)
        self.login_layout.setSpacing(20)
        
        # 登录框标题
        self.login_title = QLabel("用户登录")
        self.login_title.setObjectName("loginTitleLabel")
        self.login_title.setAlignment(Qt.AlignCenter)
        self.login_layout.addWidget(self.login_title)
        
        self.login_layout.addSpacing(20)
        
        # 用户名区域
        self.label_2 = QLabel("用户名")
        self.label_2.setObjectName("fieldLabel")
        self.login_layout.addWidget(self.label_2)
        
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("请输入用户名...")
        self.lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.login_layout.addWidget(self.lineEdit)
        
        self.login_layout.addSpacing(10)
        
        # 密码区域
        self.label_3 = QLabel("密  码")
        self.label_3.setObjectName("fieldLabel")
        self.login_layout.addWidget(self.label_3)
        
        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_2.setPlaceholderText("请输入密码...")
        self.lineEdit_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.login_layout.addWidget(self.lineEdit_2)
        
        self.login_layout.addSpacing(30)
        
        # 登录按钮
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        self.pushButton = QPushButton("登 录")
        self.pushButton.setObjectName("loginBtn")
        self.pushButton.setCursor(Qt.PointingHandCursor)
        self.pushButton.setMinimumSize(200, 55)
        # 添加按钮发光效果
        btn_glow = QGraphicsDropShadowEffect()
        btn_glow.setBlurRadius(15)
        btn_glow.setColor(QColor(157, 214, 224, 120))
        btn_glow.setOffset(0, 3)
        self.pushButton.setGraphicsEffect(btn_glow)
        self.btn_layout.addWidget(self.pushButton)
        self.btn_layout.addStretch()
        self.login_layout.addLayout(self.btn_layout)
        
        self.login_layout.addStretch()
        
        self.content_layout.addWidget(self.login_frame)
        self.content_layout.addStretch(1)  # 右侧弹性空间
        
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

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        # 设置背景图片初始位置和大小
        self._update_background()
        MainWindow.resizeEvent = self._on_resize

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
    def _update_background(self):
        """ 更新背景图片大小和位置 """
        if hasattr(self, 'background_label') and hasattr(self, 'centralwidget'):
            size = self.centralwidget.size()
            self.background_label.setGeometry(0, 0, size.width(), size.height())
            # 缩放背景图片
            scaled_bg = self.background_pixmap.scaled(
                size.width(), size.height(),
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            
            w, h = scaled_bg.width(), scaled_bg.height()
            
            # 添加统一的半透明白色遮罩
            painter = QPainter(scaled_bg)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 255, 255, 150)))  # 白色半透明遮罩
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, w, h)
            painter.end()
            
            self.background_label.setPixmap(scaled_bg)
            self.background_label.lower()  # 确保背景在最底层
    
    def _on_resize(self, event):
        """ 窗口大小改变时更新背景 """
        self._update_background()
        # 调用原始的resizeEvent
        QtWidgets.QWidget.resizeEvent(self.centralwidget, event)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "工业缺陷类别预测系统"))
        self.label.setText(_translate("MainWindow", "工业缺陷类别预测系统"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
