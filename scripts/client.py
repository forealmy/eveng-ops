"""
EVE-NG 连接客户端 - M1 模块
封装 EVE-NG API 的连接管理功能
"""

import json
import os
from typing import Optional

try:
    import evengsdk
    from evengsdk.client import EvengClient
except ImportError:
    raise ImportError("请先安装 eve-ng SDK: pip install eve-ng")


class EVEClient:
    """EVE-NG 连接客户端"""

    def __init__(self, host: str, username: str, password: str, ssl_verify: bool = False, timeout: int = 30):
        # 移除协议前缀，EvengClient 会自动添加 http://
        self.host = host.replace("http://", "").replace("https://", "")
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.timeout = timeout
        self._connected = False
        self.client = evengsdk.client.EvengClient(self.host, ssl_verify=ssl_verify)

    @classmethod
    def from_config(cls, config_path: Optional[str] = None) -> "EVEClient":
        """从配置文件加载"""
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "eveng_config.json")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        return cls(
            host=config["host"],
            username=config["username"],
            password=config["password"],
            ssl_verify=config.get("ssl_verify", False),
            timeout=config.get("timeout", 30)
        )

    def connect(self) -> None:
        """登录并保存会话"""
        self.client.login(self.username, self.password)
        self._connected = True

    def disconnect(self) -> None:
        """登出"""
        self.client.logout()
        self._connected = False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    def get_status(self) -> dict:
        """获取服务器状态"""
        return self.client.api.get_server_status()

    def list_folders(self) -> dict:
        """列出所有文件夹（含实验室）"""
        return self.client.api.list_folders()

    def list_labs(self) -> list:
        """列出所有实验"""
        folders_data = self.client.api.list_folders()
        data = folders_data.get("data", {})
        labs = data.get("labs", [])
        # 也递归获取子文件夹中的 labs
        for folder in data.get("folders", []):
            folder_path = folder.get("path", "")
            if folder_path:
                try:
                    folder_data = self.client.api.get_folder(folder_path)
                    folder_labs = folder_data.get("data", {}).get("labs", [])
                    for lab in folder_labs:
                        lab["source_folder"] = folder_path
                        labs.append(lab)
                except Exception:
                    pass
        return labs

    def get_lab(self, path: str) -> dict:
        """获取实验详情

        :param path: 实验室路径，如 "/myfolder/mylab.unl"
        :type path: str
        """
        return self.client.api.get_lab(path)

    def __repr__(self) -> str:
        return f"EVEClient(host={self.host}, username={self.username}, connected={self._connected})"
