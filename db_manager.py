"""
数据库管理模块 - 管理缺陷识别历史记录
使用 SQLite 存储识别结果、缩略图和统计数据
"""

import sqlite3
import os
from io import BytesIO
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "defect_history.db")


class HistoryDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                image_name TEXT NOT NULL,
                thumbnail BLOB,
                defect_class TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def add_record(self, image_path, image_name, thumbnail_bytes, defect_class, confidence):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO history (image_path, image_name, thumbnail, defect_class, confidence) VALUES (?, ?, ?, ?, ?)",
            (image_path, image_name, thumbnail_bytes, defect_class, confidence)
        )
        conn.commit()
        conn.close()

    def get_all_records(self):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, image_path, image_name, thumbnail, defect_class, confidence, created_at FROM history ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_records_by_class(self, defect_class):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, image_path, image_name, thumbnail, defect_class, confidence, created_at FROM history WHERE defect_class = ? ORDER BY created_at DESC",
            (defect_class,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_class_stats(self):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT defect_class, COUNT(*) as count FROM history GROUP BY defect_class ORDER BY count DESC"
        ).fetchall()
        conn.close()
        return {r['defect_class']: r['count'] for r in rows}

    def get_total_count(self):
        conn = self._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        conn.close()
        return count

    def get_today_count(self):
        conn = self._get_conn()
        today = date.today().isoformat()
        count = conn.execute(
            "SELECT COUNT(*) FROM history WHERE date(created_at) = ?", (today,)
        ).fetchone()[0]
        conn.close()
        return count

    def delete_record(self, record_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()

    def clear_all(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM history")
        conn.commit()
        conn.close()

    def get_recent_records(self, limit=10):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, image_path, image_name, thumbnail, defect_class, confidence, created_at FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search_records(self, keyword):
        conn = self._get_conn()
        like = "%%%s%%" % keyword
        rows = conn.execute(
            "SELECT id, image_path, image_name, thumbnail, defect_class, confidence, created_at FROM history WHERE image_name LIKE ? OR defect_class LIKE ? ORDER BY created_at DESC",
            (like, like)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def export_csv(self, filepath):
        import csv
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, image_path, image_name, defect_class, confidence, created_at FROM history ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', '图片路径', '文件名', '缺陷类别', '置信度', '识别时间'])
            for r in rows:
                writer.writerow([r['id'], r['image_path'], r['image_name'],
                                 r['defect_class'], "%.2f%%" % (r['confidence'] * 100),
                                 r['created_at']])
        return filepath
