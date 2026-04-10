"""LAN 适配层：用于把识别结果上报到工业局域网系统。"""

import json
import os
import socket
import time
import urllib.error
import urllib.request


class LanGatewayClient:
    def __init__(self, config_path):
        self._config_path = config_path
        self._config = self._load_config()

    def _default_config(self):
        return {
            "enabled": False,
            "base_url": "",
            "auth_token": "",
            "connect_timeout_sec": 2.0,
            "read_timeout_sec": 3.0,
            "endpoints": {
                "health": "/api/v1/health",
                "prediction": "/api/v1/idcs/predictions",
                "alert": "/api/v1/idcs/alerts",
            },
        }

    def _load_config(self):
        config = self._default_config()
        if not os.path.exists(self._config_path):
            return config

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                config.update({k: v for k, v in loaded.items() if k != "endpoints"})
                endpoints = loaded.get("endpoints")
                if isinstance(endpoints, dict):
                    config["endpoints"].update(endpoints)
        except Exception:
            # 配置错误时回退默认配置，保证主流程不受影响。
            pass
        return config

    def reload_config(self):
        self._config = self._load_config()

    def get_status(self):
        self.reload_config()
        base_url = str(self._config.get("base_url") or "").strip()
        return {
            "enabled": bool(self._config.get("enabled", False)),
            "base_url": base_url,
            "prediction_endpoint": self._config["endpoints"].get("prediction", ""),
            "alert_endpoint": self._config["endpoints"].get("alert", ""),
            "health_endpoint": self._config["endpoints"].get("health", ""),
        }

    def test_connection(self):
        self.reload_config()
        payload = {
            "type": "idcs-lan-healthcheck",
            "timestamp": int(time.time()),
            "host": socket.gethostname(),
        }
        return self._post(self._config["endpoints"].get("health", "/api/v1/health"), payload)

    def report_prediction(self, payload):
        self.reload_config()
        return self._post(self._config["endpoints"].get("prediction", "/api/v1/idcs/predictions"), payload)

    def report_alert(self, payload):
        self.reload_config()
        return self._post(self._config["endpoints"].get("alert", "/api/v1/idcs/alerts"), payload)

    def _post(self, endpoint, payload):
        enabled = bool(self._config.get("enabled", False))
        base_url = str(self._config.get("base_url") or "").strip().rstrip("/")

        if not enabled:
            return {"success": False, "skipped": True, "reason": "lan disabled"}

        if not base_url:
            return {"success": False, "skipped": True, "reason": "base_url is empty"}

        endpoint = "/" + str(endpoint or "").lstrip("/")
        url = base_url + endpoint

        token = str(self._config.get("auth_token") or "").strip()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url=url, data=data, headers=headers, method="POST")

        timeout = float(self._config.get("connect_timeout_sec", 2.0)) + float(
            self._config.get("read_timeout_sec", 3.0)
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                code = int(resp.getcode() or 0)
                body = resp.read().decode("utf-8", errors="ignore")
                return {
                    "success": 200 <= code < 300,
                    "status_code": code,
                    "response": body[:500],
                    "url": url,
                }
        except urllib.error.HTTPError as exc:
            try:
                err_body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body = str(exc)
            return {
                "success": False,
                "status_code": int(getattr(exc, "code", 0) or 0),
                "error": err_body[:500],
                "url": url,
            }
        except Exception as exc:
            return {
                "success": False,
                "status_code": 0,
                "error": str(exc),
                "url": url,
            }
