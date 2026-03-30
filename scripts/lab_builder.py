"""
EVE-NG 拓扑构建器 - M2 模块
根据 YAML/JSON 定义批量创建节点+网络+链路
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    from .client import EVEClient
except ImportError:
    from client import EVEClient  # noqa: F401


class LabBuilder:
    """EVE-NG 拓扑构建器"""

    def __init__(self, client: EVEClient):
        self.client = client

    # -------------------------------------------------------------------------
    # Lab 管理
    # -------------------------------------------------------------------------

    def create_lab(
        self,
        lab_name: str,
        lab_path: str = "/",
        author: str = "",
        description: str = "",
    ) -> Dict:
        """创建实验

        :param lab_name: 实验名称
        :param lab_path: 保存路径，默认 /
        :param author: 作者
        :param description: 描述
        :return: API 响应
        """
        resp = self.client.client.api.create_lab(
            name=lab_name,
            path=lab_path,
            author=author,
            description=description,
        )
        return resp

    def delete_lab(self, lab_path: str) -> Dict:
        """删除实验

        :param lab_path: 实验路径，如 "/test_lab.unl"
        :return: API 响应
        """
        return self.client.client.api.delete_lab(lab_path)

    def lab_exists(self, lab_path: str) -> bool:
        """检查实验是否存在"""
        try:
            resp = self.client.get_lab(lab_path)
            return resp.get("status") == "success"
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # 节点操作
    # -------------------------------------------------------------------------

    def create_node(
        self,
        lab_path: str,
        name: str,
        template: str,
        image: Optional[str] = None,
        ram: Optional[int] = None,
        cpu: Optional[int] = None,
        ethernet: Optional[int] = None,
        serial: Optional[int] = None,
        node_type: str = "qemu",
        console: str = "telnet",
        icon: Optional[str] = None,
        delay: int = 0,
        left: Optional[int] = None,
        top: Optional[int] = None,
    ) -> Dict:
        """创建单个节点

        :param lab_path: 实验路径
        :param name: 节点名称
        :param template: 模板名称，如 "qemu", "docker", "iol", "vpcs"
        :param image: 镜像名称（可选）
        :param ram: 内存 MB（可选）
        :param cpu: CPU 数量（可选）
        :param ethernet: 以太网接口组数（可选，每组4个接口）
        :param serial: 串行接口组数（可选）
        :param node_type: 节点类型，默认 qemu
        :param console: 控制台类型，默认 telnet
        :param icon: 图标（可选）
        :param delay: 启动延迟秒数
        :param left: 左偏移百分比
        :param top: 顶部偏移百分比
        :return: API 响应
        """
        kwargs = {
            "path": lab_path,
            "name": name,
            "template": template,
            "node_type": node_type,
            "console": console,
            "delay": delay,
        }

        if image is not None:
            kwargs["image"] = image
        if ram is not None:
            kwargs["ram"] = ram
        if cpu is not None:
            kwargs["cpu"] = cpu
        if ethernet is not None:
            kwargs["ethernet"] = ethernet
        if serial is not None:
            kwargs["serial"] = serial
        if icon is not None:
            kwargs["icon"] = icon
        if left is not None:
            kwargs["left"] = left
        if top is not None:
            kwargs["top"] = top

        resp = self.client.client.api.add_node(**kwargs)
        return resp

    def list_nodes(self, lab_path: str) -> Dict:
        """列出实验中的所有节点"""
        return self.client.client.api.list_nodes(lab_path)

    def get_node_by_name(self, lab_path: str, name: str) -> Optional[Dict]:
        """按名称获取节点"""
        return self.client.client.api.get_node_by_name(lab_path, name)

    def delete_node(self, lab_path: str, node_id: str) -> Dict:
        """删除节点"""
        return self.client.client.api.delete_node(lab_path, node_id)

    # -------------------------------------------------------------------------
    # 网络操作
    # -------------------------------------------------------------------------

    def create_network(
        self,
        lab_path: str,
        name: str,
        network_type: str = "bridge",
        visibility: int = 0,
        left: Optional[int] = None,
        top: Optional[int] = None,
    ) -> Dict:
        """创建网络

        :param lab_path: 实验路径
        :param name: 网络名称
        :param network_type: 网络类型（bridge, pnet, ovs, etc.）
        :param visibility: 可视化，0=隐藏，1=显示
        :param left: 左偏移百分比
        :param top: 顶部偏移百分比
        :return: API 响应
        """
        return self.client.client.api.add_lab_network(
            path=lab_path,
            name=name,
            network_type=network_type,
            visibility=visibility,
            left=left,
            top=top,
        )

    def list_networks(self, lab_path: str) -> Dict:
        """列出实验中的所有网络"""
        return self.client.client.api.list_lab_networks(lab_path)

    def get_network_by_name(self, lab_path: str, name: str) -> Optional[Dict]:
        """按名称获取网络"""
        return self.client.client.api.get_lab_network_by_name(lab_path, name)

    def delete_network(self, lab_path: str, net_id: int) -> Dict:
        """删除网络"""
        return self.client.client.api.delete_lab_network(lab_path, net_id)

    # -------------------------------------------------------------------------
    # 链路操作
    # -------------------------------------------------------------------------

    def connect(
        self,
        lab_path: str,
        node1: str,
        iface1: str,
        node2: str,
        iface2: Optional[str] = None,
        dst_type: str = "network",
    ) -> Dict:
        """连接两个节点，或将节点连接到网络

        用法：
          # 连接节点到网络
          builder.connect(lab_path, "Router1", "eth0", "WAN")
          # 连接两个节点
          builder.connect(lab_path, "Router1", "eth0", "Router2", "eth0", dst_type="node")

        :param lab_path: 实验路径
        :param node1: 源节点名称
        :param iface1: 源接口名称
        :param node2: 目标（网络名称或节点名称）
        :param iface2: 目标接口（dst_type=node 时必填）
        :param dst_type: "network" 或 "node"
        :return: API 响应
        """
        if dst_type == "node":
            return self.client.client.api.connect_node_to_node(
                path=lab_path,
                src=node1,
                src_label=iface1,
                dst=node2,
                dst_label=iface2,
            )
        else:
            return self.client.client.api.connect_node_to_cloud(
                path=lab_path,
                src=node1,
                src_label=iface1,
                dst=node2,
            )

    def connect_by_list(
        self, lab_path: str, links: List[Tuple]
    ) -> List[Dict]:
        """批量连接

        links 格式：
          - [node1, iface1, network_name]  → 节点连网络
          - [node1, iface1, node2, iface2] → 节点连节点

        :param lab_path: 实验路径
        :param links: 链路定义列表
        :return: 各链路连接结果列表
        """
        results = []
        for link in links:
            if len(link) == 3:
                node1, iface1, network = link
                resp = self.connect(lab_path, node1, iface1, network)
            elif len(link) == 4:
                node1, iface1, node2, iface2 = link
                resp = self.connect(
                    lab_path, node1, iface1, node2, iface2, dst_type="node"
                )
            else:
                resp = {"status": "error", "message": f"Invalid link format: {link}"}
            results.append(resp)
        return results

    # -------------------------------------------------------------------------
    # 拓扑构建（核心方法）
    # -------------------------------------------------------------------------

    def build_from_dict(
        self,
        topo_def: Dict[str, Any],
        lab_path: str = "/",
    ) -> Dict[str, Any]:
        """从 dict/JSON 构建完整拓扑

        topo_def 格式：
        {
          "lab_name": "my_lab",
          "author": "admin",
          "description": "...",
          "nodes": [
            {"name": "Router1", "template": "qemu", "image": "...", ...}
          ],
          "networks": [
            {"name": "WAN", "type": "bridge"}
          ],
          "links": [
            ["Router1", "eth0", "WAN"],
            ["Router1", "eth1", "LAN"]
          ]
        }

        :param topo_def: 拓扑定义字典
        :param lab_path: 实验室路径前缀，默认 /
        :return: 构建结果报告
        """
        lab_name = topo_def.get("lab_name", "untitled_lab")
        author = topo_def.get("author", "")
        description = topo_def.get("description", "")
        nodes = topo_def.get("nodes", [])
        networks = topo_def.get("networks", [])
        links = topo_def.get("links", [])

        # 1. 创建实验室
        # 避免 // 导致 Windows UNC 路径问题
        lab_full_path = f"{lab_path.rstrip('/')}/{lab_name}.unl"
        if not self.lab_exists(lab_full_path):
            create_resp = self.create_lab(
                lab_name=lab_name,
                lab_path=lab_path,
                author=author,
                description=description,
            )
        else:
            create_resp = {"status": "already_exists", "message": f"Lab {lab_name} already exists"}

        # 2. 创建网络
        network_results = []
        name_to_net_id = {}
        for net in networks:
            net_name = net.get("name")
            net_type = net.get("type", "bridge")
            visibility = net.get("visibility", 0)
            try:
                resp = self.create_network(
                    lab_path=lab_full_path,
                    name=net_name,
                    network_type=net_type,
                    visibility=visibility,
                    left=net.get("left"),
                    top=net.get("top"),
                )
                if resp.get("status") == "success":
                    net_info = self.get_network_by_name(lab_full_path, net_name)
                    name_to_net_id[net_name] = net_info["id"] if net_info else None
                network_results.append({"name": net_name, "result": resp})
            except Exception as e:
                # 网络可能已存在，跳过
                network_results.append({"name": net_name, "result": {"status": "skipped", "message": str(e)}})

        # 3. 创建节点
        node_results = []
        name_to_node_id = {}
        for node in nodes:
            node_name = node.get("name")
            try:
                resp = self.create_node(
                    lab_path=lab_full_path,
                    name=node_name,
                    template=node.get("template", "qemu"),
                    image=node.get("image"),
                    ram=node.get("ram"),
                    cpu=node.get("cpu"),
                    ethernet=node.get("ethernet"),
                    serial=node.get("serial"),
                    node_type=node.get("type", "qemu"),
                    console=node.get("console", "telnet"),
                    icon=node.get("icon"),
                    delay=node.get("delay", 0),
                    left=node.get("left"),
                    top=node.get("top"),
                )
                node_results.append({"name": node_name, "result": resp})
                # 获取 node_id
                node_info = self.get_node_by_name(lab_full_path, node_name)
                name_to_node_id[node_name] = node_info["id"] if node_info else None
            except Exception as e:
                node_results.append({"name": node_name, "result": {"status": "error", "message": str(e)}})

        # 4. 创建链路
        link_results = []
        for link in links:
            try:
                if len(link) == 3:
                    node1, iface1, network_name = link
                    resp = self.connect(lab_full_path, node1, iface1, network_name)
                    link_results.append({"link": link, "result": resp})
                elif len(link) == 4:
                    node1, iface1, node2, iface2 = link
                    resp = self.connect(lab_full_path, node1, iface1, node2, iface2, dst_type="node")
                    link_results.append({"link": link, "result": resp})
                else:
                    link_results.append({"link": link, "result": {"status": "error", "message": "Invalid link format"}})
            except Exception as e:
                link_results.append({"link": link, "result": {"status": "error", "message": str(e)}})

        return {
            "lab_path": lab_full_path,
            "lab_created": create_resp,
            "networks": network_results,
            "nodes": node_results,
            "links": link_results,
        }

    def build_from_yaml(
        self,
        yaml_path: str,
        lab_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """从 YAML 文件构建实验拓扑

        :param yaml_path: YAML 文件路径
        :param lab_name: 可覆盖 lab_name
        :return: 构建结果报告
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            topo_def = yaml.safe_load(f)

        if lab_name:
            topo_def["lab_name"] = lab_name

        return self.build_from_dict(topo_def)

    # -------------------------------------------------------------------------
    # 实用工具
    # -------------------------------------------------------------------------

    def list_templates(self) -> Dict:
        """列出所有可用模板"""
        return self.client.client.api.list_node_templates()

    def list_network_types(self) -> List[str]:
        """列出所有网络类型"""
        return self.client.client.api.network_types

    def get_lab_topology(self, lab_path: str) -> Dict:
        """获取实验室拓扑信息"""
        return self.client.client.api.get_lab_topology(lab_path)

    def __repr__(self) -> str:
        return f"LabBuilder(client={self.client})"
