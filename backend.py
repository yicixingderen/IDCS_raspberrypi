"""
后端 API 模块 - 通过 pywebview 暴露给 JavaScript 调用
所有非公开属性以 _ 开头，避免 pywebview 递归遍历导致栈溢出
"""

import os
import base64
import io
from datetime import datetime

import webview
from PIL import Image

from db_manager import HistoryDB
from lan_gateway import LanGatewayClient
from predict import predict_

try:
    import numpy as np
except ImportError:
    np = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CAMERA_READ_FAIL_LIMIT = 10
CAMERA_SCAN_INDICES = (0, 1, 2, 3, 4, 5)
CAMERA_DEVICE_INDEX = 0

def _read_alert_threshold(default=0.85):
    raw = os.getenv("IDCS_ALERT_THRESHOLD", str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        return default
    if 0.0 <= value <= 1.0:
        return value
    return default


ALERT_THRESHOLD = _read_alert_threshold()


class Api:
    def __init__(self):
        self._db = HistoryDB()
        self._window = None

        self._camera_capture = None
        self._picam2 = None
        self._camera_backend = None
        self._camera_active = False
        self._frame_read_failures = 0
        self._last_alert_print_at = None

        self._lan = LanGatewayClient(os.path.join(BASE_DIR, 'lan_gateway_config.json'))

    def set_window(self, window):
        self._window = window

    # ─── Auth ───

    def login(self, username, password):
        if username and password:
            return {'success': True}
        return {'success': False, 'message': '请输入用户名和密码'}

    # ─── LAN Integration ───

    def get_lan_status(self):
        return self._lan.get_status()

    def test_lan_connection(self):
        return self._lan.test_connection()

    def _report_lan_prediction(self, payload):
        try:
            self._lan.report_prediction(payload)
        except Exception:
            # LAN 上报失败不影响主流程
            pass

    def _report_lan_alert(self, payload):
        try:
            self._lan.report_alert(payload)
        except Exception:
            # LAN 上报失败不影响主流程
            pass

    # ─── File Selection ───

    def select_image(self):
        file_types = ('图片文件 (*.jpg;*.jpeg;*.png;*.bmp;*.tif;*.tiff)',)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            directory=self._default_dir(),
            file_types=file_types
        )
        if result and len(result) > 0:
            path = result[0]
            b64 = self._image_to_base64(path)
            return {'path': path, 'name': os.path.basename(path), 'base64': b64}
        return None

    def select_images(self):
        file_types = ('图片文件 (*.jpg;*.jpeg;*.png;*.bmp;*.tif;*.tiff)',)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            directory=self._default_dir(),
            file_types=file_types,
            allow_multiple=True
        )
        if result and len(result) > 0:
            images = []
            for path in result:
                b64 = self._image_to_base64(path)
                images.append({'path': path, 'name': os.path.basename(path), 'base64': b64})
            return images
        return None

    def _default_dir(self):
        d = os.path.join(BASE_DIR, 'data', 'test')
        return d if os.path.exists(d) else BASE_DIR

    # ─── Prediction ───

    def predict_single(self, image_path):
        img = Image.open(image_path)
        class_name, confidence = predict_(img)

        thumb_bytes = self._make_thumbnail(img)
        image_name = os.path.basename(image_path)
        self._db.add_record(image_path, image_name, thumb_bytes, class_name, float(confidence))

        self._report_lan_prediction({
            'source': 'web-single',
            'image_path': image_path,
            'image_name': image_name,
            'class_name': class_name,
            'confidence': float(confidence),
            'threshold': ALERT_THRESHOLD,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
        })

        return {
            'class_name': class_name,
            'confidence': float(confidence),
            'image_name': image_name,
            'image_path': image_path
        }

    def predict_batch(self, image_paths):
        results = []
        for path in image_paths:
            try:
                r = self.predict_single(path)
                r['success'] = True
                results.append(r)
            except Exception as e:
                results.append({
                    'success': False,
                    'image_path': path,
                    'image_name': os.path.basename(path),
                    'error': str(e)
                })
        return results

    # ─── Camera (Web) ───

    def start_camera(self):
        if self._camera_active:
            return {
                'success': True,
                'backend': self._camera_backend,
                'message': f'摄像头已开启({self._camera_backend})，正在实时预测',
                'threshold': ALERT_THRESHOLD,
            }

        self._camera_capture = None
        self._picam2 = None
        self._camera_backend = None

        picam2 = self._probe_picamera2()
        if picam2 is not None:
            self._picam2 = picam2
            self._camera_backend = 'Picamera2'
        else:
            capture, backend_desc = self._probe_opencv_camera()
            if capture is not None:
                self._camera_capture = capture
                self._camera_backend = backend_desc
            else:
                if cv2 is None and Picamera2 is None:
                    return {'success': False, 'message': '未安装 OpenCV/Picamera2，无法开启摄像头'}
                if Picamera2 is None and cv2 is not None:
                    return {'success': False, 'message': 'Picamera2 不可用，且 OpenCV 摄像头读取失败'}
                if cv2 is None:
                    return {'success': False, 'message': 'OpenCV 不可用，且 Picamera2 启动失败'}
                return {'success': False, 'message': '摄像头打开失败，请检查连接或相机接口配置'}

        self._camera_active = True
        self._frame_read_failures = 0
        self._last_alert_print_at = None

        return {
            'success': True,
            'backend': self._camera_backend,
            'message': f'摄像头已开启({self._camera_backend})，正在实时预测',
            'threshold': ALERT_THRESHOLD,
        }

    def stop_camera(self):
        if self._camera_capture is not None:
            self._camera_capture.release()
            self._camera_capture = None

        if self._picam2 is not None:
            try:
                self._picam2.stop()
            except Exception:
                pass
            try:
                self._picam2.close()
            except Exception:
                pass
            self._picam2 = None

        self._camera_backend = None
        self._camera_active = False
        self._frame_read_failures = 0
        self._last_alert_print_at = None

        return {'success': True, 'message': '摄像头已关闭'}

    def get_camera_frame(self):
        if not self._camera_active:
            return {'success': False, 'message': '摄像头未开启'}

        rgb_frame = self._read_camera_rgb_frame()
        if rgb_frame is None:
            self._frame_read_failures += 1
            if self._frame_read_failures >= CAMERA_READ_FAIL_LIMIT:
                self.stop_camera()
                return {
                    'success': False,
                    'message': '摄像头读取失败，请检查摄像头占用或分辨率',
                    'stopped': True,
                }
            return {'success': False, 'message': '摄像头预热中...'}

        self._frame_read_failures = 0

        try:
            result_type, confidence = predict_(Image.fromarray(rgb_frame))
        except Exception as exc:
            return {'success': False, 'message': f'预测失败: {exc}'}

        confidence = float(confidence)
        is_alert = confidence > ALERT_THRESHOLD
        display_class = result_type if is_alert else '未检测到异常'

        if is_alert:
            now = datetime.now()
            if self._last_alert_print_at is None or (now - self._last_alert_print_at).total_seconds() >= 1:
                print(
                    f"异常类型: {result_type} | 发生时间: {now.strftime('%Y-%m-%d %H:%M:%S')} | 准确率: {confidence:.4f}"
                )
                self._last_alert_print_at = now
            status_text = f'检测到异常: {result_type}'

            self._report_lan_alert({
                'source': 'web-camera',
                'camera_backend': self._camera_backend,
                'class_name': result_type,
                'confidence': confidence,
                'threshold': ALERT_THRESHOLD,
                'status': status_text,
                'timestamp': now.isoformat(timespec='seconds'),
            })
        else:
            self._last_alert_print_at = None
            status_text = '未检测到异常'

        return {
            'success': True,
            'backend': self._camera_backend,
            'frame_base64': self._rgb_frame_to_base64(rgb_frame),
            'class_name': result_type,
            'display_class': display_class,
            'confidence': confidence,
            'alert': is_alert,
            'status': status_text,
            'threshold': ALERT_THRESHOLD,
        }

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

    def _read_camera_rgb_frame(self):
        if self._camera_capture is not None:
            ret, frame = self._camera_capture.read()
            if not ret or frame is None:
                return None
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self._picam2 is not None:
            try:
                frame = self._picam2.capture_array()
            except Exception:
                return None

            if frame is None:
                return None

            if frame.ndim == 2:
                if np is None:
                    return None
                frame = np.stack((frame, frame, frame), axis=-1)
            elif frame.ndim == 3 and frame.shape[2] >= 3:
                frame = frame[:, :, :3]
            else:
                return None

            if np is not None:
                return np.ascontiguousarray(frame)
            return frame

        return None

    # ─── History ───

    def get_history(self):
        records = self._db.get_all_records()
        return self._serialize_records(records)

    def get_history_by_class(self, class_name):
        records = self._db.get_records_by_class(class_name)
        return self._serialize_records(records)

    def search_history(self, keyword):
        records = self._db.search_records(keyword)
        return self._serialize_records(records)

    def get_recent(self, limit=10):
        records = self._db.get_recent_records(limit)
        return self._serialize_records(records)

    def delete_record(self, record_id):
        self._db.delete_record(record_id)
        return {'success': True}

    def clear_history(self):
        self._db.clear_all()
        return {'success': True}

    def export_csv(self):
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=BASE_DIR,
            save_filename='defect_history.csv',
            file_types=('CSV 文件 (*.csv)',)
        )
        if result:
            filepath = result[0] if isinstance(result, (list, tuple)) else result
            self._db.export_csv(filepath)
            return {'success': True, 'path': filepath}
        return {'success': False}

    # ─── Stats ───

    def get_stats(self):
        return {
            'total': self._db.get_total_count(),
            'today': self._db.get_today_count(),
            'class_stats': self._db.get_class_stats()
        }

    # ─── Image Utils ───

    def get_image_base64(self, path):
        if os.path.exists(path):
            return self._image_to_base64(path)
        return None

    def _image_to_base64(self, path):
        with open(path, 'rb') as f:
            data = f.read()
        ext = os.path.splitext(path)[1].lower()
        mime = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png',
                '.bmp': 'bmp', '.tif': 'tiff', '.tiff': 'tiff'}.get(ext, 'jpeg')
        return 'data:image/%s;base64,%s' % (mime, base64.b64encode(data).decode())

    def _rgb_frame_to_base64(self, rgb_frame):
        img = Image.fromarray(rgb_frame)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

    def _make_thumbnail(self, img):
        thumb = img.copy()
        thumb.thumbnail((128, 128))
        if thumb.mode != 'RGB':
            thumb = thumb.convert('RGB')
        buf = io.BytesIO()
        thumb.save(buf, format='JPEG', quality=85)
        return buf.getvalue()

    def _serialize_records(self, records):
        serialized = []
        for r in records:
            item = {
                'id': r['id'],
                'image_path': r['image_path'],
                'image_name': r['image_name'],
                'defect_class': r['defect_class'],
                'confidence': r['confidence'],
                'created_at': r['created_at'],
            }
            if r.get('thumbnail'):
                item['thumbnail'] = 'data:image/jpeg;base64,' + base64.b64encode(r['thumbnail']).decode()
            else:
                item['thumbnail'] = None
            serialized.append(item)
        return serialized

    # ─── Device Info ───

    def get_device_info(self):
        import torch
        return {
            'device': 'CUDA' if torch.cuda.is_available() else 'CPU',
            'model': 'Mobile_Shuffle + EPSA'
        }

    def __del__(self):
        try:
            self.stop_camera()
        except Exception:
            pass
