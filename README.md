# IDCS_rasp

工业缺陷分类系统在 Raspberry Pi 5 (Debian) 的集成版本。

本目录已集成两套能力：
- PyQt 桌面端流程（原 IDCS_rasp）：登录、单图预测、摄像头实时检测。
- WebView 前端流程（迁移自 IDCS_demo）：Web 界面、单图/批量预测、历史记录、统计、CSV 导出、实时摄像头检测。

## 目录说明
- enterLogin.py: PyQt 桌面端入口
- mainprogress.py: PyQt 主界面与预测流程
- app.py: WebView 入口（加载 web/index.html）
- backend.py: WebView 后端 API（含摄像头接口）
- db_manager.py: SQLite 历史记录管理
- web/: Web 前端静态资源
- predict.py: 模型加载与推理
- net_070.pth: 训练权重
- setup_debian.sh: Debian 环境安装脚本
- run_idcs.sh: PyQt 桌面端启动脚本
- run_web.sh: WebView 启动脚本

## 首次部署
1. 进入目录
   cd IDCS_rasp
2. 初始化环境
   ./setup_debian.sh

## 运行
- 桌面端（PyQt）
  ./run_idcs.sh
- Web 端（pywebview）
  ./run_web.sh

## 摄像头实时检测
- 统一策略：优先尝试 OpenCV，失败后自动切换到 Picamera2。
- 统一阈值：当预测置信度 > 0.85 时判定为异常，并在终端输出异常类型、发生时间、准确率。
- 当预测置信度 <= 0.85 时显示“未检测到异常”。

### PyQt 端
- 点击“开启摄像头”开始实时采集与预测。
- 点击“关闭摄像头”停止实时检测。

### Web 端
- 进入“缺陷识别”页，点击“开启摄像头”。
- 实时画面会显示在预览区，预测结果和置信度会实时刷新。
- 点击“关闭摄像头”可释放设备。
