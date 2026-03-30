"""
EVE-NG 实验环境控制 - M3 模块
实现实验环境启停控制和节点精细化管理
"""

from typing import Dict, List, Optional, Tuple

try:
    from .client import EVEClient
except ImportError:
    from client import EVEClient  # noqa: F401


class LabController:
    """EVE-NG 实验环境控制器

    提供单节点控制、批量控制、实验控制、状态监控等能力。
    """

    def __init__(self, client: EVEClient):
        self.client = client

    # -------------------------------------------------------------------------
    # 内部工具
    # -------------------------------------------------------------------------

    def _normalize_nodes(self, nodes_data: dict) -> List[dict]:
        """将 list_nodes API 返回的 data 规范化为 list[dict]"""
        nodes = nodes_data.get("data", {})
        if isinstance(nodes, dict):
            # {"3": {...}, "4": {...}} -> [{...}, {...}]
            return list(nodes.values())
        elif isinstance(nodes, list):
            return nodes
        return []

    def _resolve_node_id(self, lab_path: str, node_name: str) -> Optional[str]:
        """根据节点名称解析 node_id"""
        node_info = self.client.client.api.get_node_by_name(lab_path, node_name)
        if node_info and "id" in node_info:
            return str(node_info["id"])
        return None

    def _resolve_all_node_ids(self, lab_path: str) -> List[Tuple[str, str]]:
        """解析实验中所有节点的 (name, node_id)"""
        result = []
        nodes_data = self.client.client.api.list_nodes(lab_path)
        for node in self._normalize_nodes(nodes_data):
            name = node.get("name", "")
            node_id = node.get("id", "")
            if name and node_id:
                result.append((name, str(node_id)))
        return result

    @staticmethod
    def _node_status_text(status: int) -> str:
        """将数值状态转为可读文本"""
        status_map = {
            0: "stopped",
            1: "starting",
            2: "stopping",
            3: "running",
            4: "paused",
            5: "saving",
            6: "saved",
            99: "error",
        }
        return status_map.get(status, f"unknown({status})")

    # -------------------------------------------------------------------------
    # 单节点控制
    # -------------------------------------------------------------------------

    def start_node(self, lab_path: str, node_name: str) -> Dict:
        """启动指定节点

        :param lab_path: 实验路径，如 "/HW/tst.unl"
        :param node_name: 节点名称
        :return: API 响应
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found"}
        return self.client.client.api.start_node(lab_path, node_id)

    def stop_node(self, lab_path: str, node_name: str) -> Dict:
        """停止指定节点

        :param lab_path: 实验路径
        :param node_name: 节点名称
        :return: API 响应
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found"}
        return self.client.client.api.stop_node(lab_path, node_id)

    def wipe_node(self, lab_path: str, node_name: str) -> Dict:
        """清除节点配置（恢复初始状态）

        :param lab_path: 实验路径
        :param node_name: 节点名称
        :return: API 响应
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found"}
        return self.client.client.api.wipe_node(lab_path, node_id)

    def get_node_status(self, lab_path: str, node_name: str) -> Dict:
        """获取节点运行状态

        :param lab_path: 实验路径
        :param node_name: 节点名称
        :return: 包含状态信息的字典
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found"}
        try:
            node_info = self.client.client.api.get_node_by_name(lab_path, node_name)
            if node_info:
                status_code = node_info.get("status", 0)
                return {
                    "status": "success",
                    "name": node_name,
                    "node_id": node_id,
                    "run_status": status_code,
                    "run_status_text": self._node_status_text(status_code),
                    "data": node_info,
                }
            return {"status": "error", "message": "Failed to get node info"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # 批量控制
    # -------------------------------------------------------------------------

    def start_all_nodes(self, lab_path: str) -> List[Dict]:
        """启动实验内所有节点

        :param lab_path: 实验路径
        :return: 各节点启动结果列表
        """
        results = []
        for name, node_id in self._resolve_all_node_ids(lab_path):
            try:
                resp = self.client.client.api.start_node(lab_path, node_id)
                results.append({"name": name, "node_id": node_id, "result": resp})
            except Exception as e:
                results.append({"name": name, "node_id": node_id, "result": {"status": "error", "message": str(e)}})
        return results

    def stop_all_nodes(self, lab_path: str) -> List[Dict]:
        """停止实验内所有节点

        :param lab_path: 实验路径
        :return: 各节点停止结果列表
        """
        results = []
        for name, node_id in self._resolve_all_node_ids(lab_path):
            try:
                resp = self.client.client.api.stop_node(lab_path, node_id)
                results.append({"name": name, "node_id": node_id, "result": resp})
            except Exception as e:
                results.append({"name": name, "node_id": node_id, "result": {"status": "error", "message": str(e)}})
        return results

    def wipe_all_nodes(self, lab_path: str) -> List[Dict]:
        """重置所有节点（清除配置）

        :param lab_path: 实验路径
        :return: 各节点重置结果列表
        """
        results = []
        for name, node_id in self._resolve_all_node_ids(lab_path):
            try:
                resp = self.client.client.api.wipe_node(lab_path, node_id)
                results.append({"name": name, "node_id": node_id, "result": resp})
            except Exception as e:
                results.append({"name": name, "node_id": node_id, "result": {"status": "error", "message": str(e)}})
        return results

    # -------------------------------------------------------------------------
    # 实验控制
    # -------------------------------------------------------------------------

    def start_lab(self, lab_path: str) -> Dict:
        """一键启动整个实验（启动所有节点）

        :param lab_path: 实验路径
        :return: API 响应
        """
        return self.client.client.api.start_lab(lab_path)

    def stop_lab(self, lab_path: str) -> Dict:
        """一键停止整个实验（停止所有节点）

        :param lab_path: 实验路径
        :return: API 响应
        """
        return self.client.client.api.stop_lab(lab_path)

    # -------------------------------------------------------------------------
    # 状态监控
    # -------------------------------------------------------------------------

    def get_lab_status(self, lab_path: str) -> Dict:
        """获取实验整体状态

        :param lab_path: 实验路径
        :return: 包含整体状态信息的字典
        """
        try:
            lab_info = self.client.get_lab(lab_path)
            nodes_data = self.client.client.api.list_nodes(lab_path)
            node_items = self._normalize_nodes(nodes_data)

            running = sum(1 for n in node_items if n.get("status") == 3)
            stopped = sum(1 for n in node_items if n.get("status") == 0)
            total = len(node_items)

            return {
                "status": "success",
                "lab_path": lab_path,
                "total_nodes": total,
                "running_nodes": running,
                "stopped_nodes": stopped,
                "node_summary": f"{running} running / {stopped} stopped / {total} total",
                "lab_info": lab_info.get("data", {}),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_node_status(self, lab_path: str) -> List[Dict]:
        """列出所有节点状态

        :param lab_path: 实验路径
        :return: 节点状态列表
        """
        try:
            nodes_data = self.client.client.api.list_nodes(lab_path)
            result = []
            for node in self._normalize_nodes(nodes_data):
                status_code = node.get("status", 0)
                result.append({
                    "name": node.get("name", ""),
                    "node_id": str(node.get("id", "")),
                    "template": node.get("template", ""),
                    "status_code": status_code,
                    "status_text": self._node_status_text(status_code),
                    "console": node.get("console", ""),
                    "ip_address": node.get("ip_address", ""),
                })
            return result
        except Exception as e:
            return [{"status": "error", "message": str(e)}]

    def __repr__(self) -> str:
        return f"LabController(client={self.client})"
