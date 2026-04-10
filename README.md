# IDCS_rasp

工业缺陷分类系统在 Raspberry Pi 5 (Debian) 的集成版本。

本目录已集成两套能力：
- PyQt 桌面端流程（原 IDCS_rasp）：登录、单图预测、摄像头实时检测。
- WebView 前端流程（迁移自 IDCS_demo）：Web 界面、单图/批量预测、历史记录、统计、CSV 导出、实时摄像头检测。

## 目录说明
- enterLogin.py: PyQt 桌面端入口
- mainprogress.py: PyQt 主界面与预测流程
- app.py: WebView 入口（加载 web/index.html）
- backend.py: WebView 后端 API（含摄像头接口与 LAN 预留接口）
- lan_gateway.py: 局域网上报适配层
- lan_gateway_config.json: 局域网适配配置文件（默认关闭）
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

## LAN 预留接口（工业局域网接入）
默认关闭，不影响当前系统功能。启用后会自动上报：
- 单图预测结果（web-single）
- 摄像头异常告警（web-camera 且 confidence > 0.85）

### 配置步骤
1. 编辑 `lan_gateway_config.json`
2. 把 `enabled` 改为 `true`
3. 把 `base_url` 设置为你的工业网关地址（例如 `http://192.168.1.100:8080`）
4. 按需配置 `auth_token` 与 `endpoints`

### 当前预留接口
- `Api.get_lan_status()`: 读取 LAN 配置状态
- `Api.test_lan_connection()`: 发送健康检查请求
- 自动上报：`report_prediction` / `report_alert`

### 默认上报路径
- health: `/api/v1/health`
- prediction: `/api/v1/idcs/predictions`
- alert: `/api/v1/idcs/alerts`

## 迁移兼容性说明
- 保留 IDCS_demo 的 Web 功能与业务逻辑（backend/db/web）。
- 保留 IDCS_rasp 的 Debian/树莓派运行入口与摄像头逻辑。
- setup_debian.sh 已补齐 pywebview(GTK) 相关依赖并修复原脚本语法问题。
