"""
EVE-NG 配置注入与快照管理 - M4 模块
提供节点配置管理和实验快照功能
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .client import EVEClient
except ImportError:
    from client import EVEClient  # noqa: F401


class ConfigManager:
    """EVE-NG 配置注入与快照管理器

    提供节点配置的上传、获取、导出，以及实验的导入导出、克隆等能力。
    """

    def __init__(self, client: EVEClient):
        self.client = client

    # -------------------------------------------------------------------------
    # 内部工具
    # -------------------------------------------------------------------------

    def _resolve_node_id(self, lab_path: str, node_name: str) -> Optional[str]:
        """根据节点名称解析 node_id"""
        node_info = self.client.client.api.get_node_by_name(lab_path, node_name)
        if node_info and "id" in node_info:
            return str(node_info["id"])
        return None

    def _normalize_nodes(self, nodes_data: dict) -> List[dict]:
        """将 list_nodes 返回的 data 规范化为 list[dict]"""
        nodes = nodes_data.get("data", {})
        if isinstance(nodes, dict):
            return list(nodes.values())
        return nodes if isinstance(nodes, list) else []

    # -------------------------------------------------------------------------
    # 配置注入
    # -------------------------------------------------------------------------

    def get_config(self, lab_path: str, node_name: str) -> Dict:
        """获取节点当前配置（从实验文件中读取）

        :param lab_path: 实验路径，如 "/HW/tst.unl"
        :param node_name: 节点名称
        :return: 包含配置内容的字典
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found in lab"}

        try:
            resp = self.client.client.api.get_node_config_by_id(lab_path, node_id)
            if resp.get("data"):
                config_data = resp["data"]
                # 配置内容可能在 data 或 config 字段
                config_text = config_data.get("config", "") or config_data.get("data", "")
                return {
                    "status": "success",
                    "node_name": node_name,
                    "node_id": node_id,
                    "config": config_text,
                    "raw": config_data,
                }
            return {"status": "success", "node_name": node_name, "node_id": node_id, "config": "", "raw": resp.get("data", {})}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_all_configs(self, lab_path: str) -> Dict:
        """获取实验内所有节点配置

        :param lab_path: 实验路径
        :return: 各节点配置字典
        """
        try:
            resp = self.client.client.api.get_node_configs(lab_path)
            configs = {}
            data = resp.get("data", {})
            if isinstance(data, dict):
                for node_id, node_data in data.items():
                    node_name = node_data.get("name", node_id)
                    config_text = node_data.get("config", "") or node_data.get("data", "")
                    configs[node_name] = {
                        "node_id": node_id,
                        "config": config_text,
                        "raw": node_data,
                    }
            return {"status": "success", "configs": configs}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def upload_config(
        self, lab_path: str, node_name: str, config: str, configset: str = "default"
    ) -> Dict:
        """上传节点配置（写入实验文件）

        :param lab_path: 实验路径
        :param node_name: 节点名称
        :param config: 配置内容字符串
        :param configset: 配置集名称（Pro 版本支持多配置集，Community 版本忽略）
        :return: API 响应
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found in lab"}

        try:
            resp = self.client.client.api.upload_node_config(
                lab_path, node_id, config, configset=configset
            )
            return {
                "status": "success" if resp.get("status") == "success" else "error",
                "node_name": node_name,
                "node_id": node_id,
                "response": resp,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def enable_startup_config(self, lab_path: str, node_name: str) -> Dict:
        """启用节点启动配置（让节点从配置启动，而非镜像默认配置）

        :param lab_path: 实验路径
        :param node_name: 节点名称
        :return: API 响应
        """
        node_id = self._resolve_node_id(lab_path, node_name)
        if not node_id:
            return {"status": "error", "message": f"Node '{node_name}' not found in lab"}

        try:
            resp = self.client.client.api.enable_node_config(lab_path, node_id)
            return {
                "status": "success" if resp.get("status") == "success" else "error",
                "node_name": node_name,
                "node_id": node_id,
                "response": resp,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def export_node_config(self, lab_path: str, node_name: str, output_path: str) -> Dict:
        """导出节点配置到本地文件

        :param lab_path: 实验路径
        :param node_name: 节点名称
        :param output_path: 本地输出文件路径
        :return: 结果字典
        """
        config_result = self.get_config(lab_path, node_name)
        if config_result.get("status") != "success":
            return config_result

        config_text = config_result.get("config", "")

        # 确保输出目录存在
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # 生成文件名前缀（节点名）
        safe_name = node_name.replace("/", "_").replace("\\", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_path and os.path.dirname(output_path):
            file_path = output_path
        else:
            file_path = os.path.join(
                out_dir if out_dir else ".", f"config_{safe_name}_{timestamp}.cfg"
            )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config_text)

        return {
            "status": "success",
            "node_name": node_name,
            "file_path": file_path,
            "bytes_written": len(config_text),
        }

    def export_all_configs(self, lab_path: str, output_dir: str) -> Dict:
        """导出实验内所有节点配置到指定目录

        :param lab_path: 实验路径
        :param output_dir: 本地输出目录
        :return: 各节点导出结果
        """
        os.makedirs(output_dir, exist_ok=True)
        lab_name = Path(lab_path).stem.replace(".unl", "")
        lab_output_dir = os.path.join(output_dir, f"{lab_name}_configs")
        os.makedirs(lab_output_dir, exist_ok=True)

        configs_result = self.get_all_configs(lab_path)
        if configs_result.get("status") != "success":
            return configs_result

        results = {}
        for node_name, info in configs_result.get("configs", {}).items():
            safe_name = node_name.replace("/", "_").replace("\\", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(lab_output_dir, f"{safe_name}_{timestamp}.cfg")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(info.get("config", ""))
                results[node_name] = {
                    "status": "success",
                    "file_path": file_path,
                    "bytes": len(info.get("config", "")),
                }
            except Exception as e:
                results[node_name] = {"status": "error", "message": str(e)}

        return {
            "status": "success",
            "lab_path": lab_path,
            "output_dir": lab_output_dir,
            "results": results,
        }

    # -------------------------------------------------------------------------
    # 快照管理
    # -------------------------------------------------------------------------

    def export_lab(self, lab_path: str, output_dir: str) -> Dict:
        """导出实验为 .unl 文件（ZIP 格式）

        :param lab_path: 实验路径，如 "/HW/tst.unl"
        :param output_dir: 本地输出目录
        :return: 导出结果
        """
        os.makedirs(output_dir, exist_ok=True)

        lab_name = Path(lab_path).stem.replace(".unl", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = os.path.join(output_dir, f"{lab_name}_{timestamp}.unl")

        try:
            success, filename = self.client.client.api.export_lab(lab_path, zip_filename)
            if success:
                return {
                    "status": "success",
                    "lab_path": lab_path,
                    "output_file": filename,
                    "full_path": os.path.abspath(filename),
                }
            return {"status": "error", "message": "Export failed", "response": filename}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def import_lab(self, unl_file: str, folder: str = "/") -> Dict:
        """导入 .unl 文件创建实验

        :param unl_file: 本地 .unl/.zip 文件路径
        :param folder: EVE-NG 目标文件夹，默认为根目录 "/"
        :return: 导入结果
        """
        if not os.path.exists(unl_file):
            return {"status": "error", "message": f"File not found: {unl_file}"}

        try:
            success = self.client.client.api.import_lab(unl_file, folder)
            if success:
                return {
                    "status": "success",
                    "source_file": unl_file,
                    "folder": folder,
                    "message": "Lab imported successfully",
                }
            return {"status": "error", "message": "Import failed", "response": success}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def clone_lab(self, source_lab: str, dest_lab_name: str, dest_folder: str = "/") -> Dict:
        """克隆实验（导出后导入为新实验）

        :param source_lab: 源实验路径，如 "/HW/tst.unl"
        :param dest_lab_name: 新实验名称（不含 .unl 扩展名）
        :param dest_folder: 目标文件夹，默认为根目录 "/"
        :return: 克隆结果
        """
        import tempfile

        # 1. 导出源实验到临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_result = self.export_lab(source_lab, tmp_dir)
            if export_result.get("status") != "success":
                return {"status": "error", "message": "Clone failed at export", "detail": export_result}

            unl_path = export_result.get("full_path")
            if not unl_path or not os.path.exists(unl_path):
                return {"status": "error", "message": "Exported file not found"}

            # 2. 重命名为目标实验名
            dest_unl = os.path.join(tmp_dir, f"{dest_lab_name}.unl")
            shutil.copy(unl_path, dest_unl)

            # 3. 导入到目标文件夹
            import_result = self.import_lab(dest_unl, dest_folder)
            if import_result.get("status") != "success":
                return {"status": "error", "message": "Clone failed at import", "detail": import_result}

            return {
                "status": "success",
                "source": source_lab,
                "dest_name": dest_lab_name,
                "dest_folder": dest_folder,
                "dest_path": f"{dest_folder}/{dest_lab_name}.unl",
            }

    # -------------------------------------------------------------------------
    # 模板
    # -------------------------------------------------------------------------

    def save_as_template(self, lab_path: str, template_name: str) -> Dict:
        """保存实验为模板（通过克隆到 Template 文件夹实现）

        EVE-NG 社区版的模板存储在 /opt/unetlab/data/Template/ 目录，
        此方法将实验导出到本地模板目录（手动导入）。

        :param lab_path: 实验路径
        :param template_name: 模板名称
        :return: 结果（包含导出的文件路径，需手动上传到服务器）
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            export_result = self.export_lab(lab_path, tmp_dir)
            if export_result.get("status") != "success":
                return export_result

            src_file = export_result.get("full_path")
            template_file = os.path.join(tmp_dir, f"{template_name}.unl")
            shutil.copy(src_file, template_file)

            return {
                "status": "success",
                "message": f"Template exported. Copy '{template_file}' to EVE-NG server's "
                           f"/opt/unetlab/data/Template/ folder and rename to .unl",
                "local_file": template_file,
                "template_name": template_name,
                "lab_path": lab_path,
            }

    def list_node_configs_summary(self, lab_path: str) -> List[Dict]:
        """列出所有节点配置摘要（名称、是否有配置、配置大小）

        :param lab_path: 实验路径
        :return: 节点配置摘要列表
        """
        try:
            nodes_data = self.client.client.api.list_nodes(lab_path)
            summary = []
            for node in self._normalize_nodes(nodes_data):
                node_id = str(node.get("id", ""))
                node_name = node.get("name", "")
                has_config = node.get("config", "Unconfigured") != "Unconfigured"
                summary.append({
                    "node_name": node_name,
                    "node_id": node_id,
                    "template": node.get("template", ""),
                    "has_custom_config": has_config,
                    "console": node.get("console", ""),
                    "ip_address": node.get("ip_address", ""),
                })
            return summary
        except Exception as e:
            return [{"status": "error", "message": str(e)}]

    def __repr__(self) -> str:
        return f"ConfigManager(client={self.client})"
