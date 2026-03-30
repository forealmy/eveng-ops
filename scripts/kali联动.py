"""
EVE-NG M5 模块：Kali-ops 联动
从 EVE-NG 获取靶场拓扑，辅助 Kali 侧渗透测试规划

功能：
  - 获取实验拓扑（节点+网络+链路）
  - 获取所有节点的 console IP 和端口
  - 找出边界节点（连接外部网络的节点）
  - 导出拓扑为 Kali-ops 可读的 JSON
  - 生成渗透测试视角的拓扑（入口点、关键资产、横移路径）
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from .client import EVEClient
except ImportError:
    from client import EVEClient  # noqa: F401


class Kali联动:
    """EVE-NG 与 Kali-ops 联动模块

    从 EVE-NG 获取靶场拓扑，为 Kali 侧渗透测试提供情报支持。
    """

    # EVE-NG 管理网络常见网段
    MANAGEMENT_NETWORKS = ["10.255.255.0/24", "172.17.0.0/16"]
    # 外部/互联网连接的网络类型
    EXTERNAL_NETWORK_TYPES = {"bridge", "ovs", "vxlan", "flat", "nat"}
    # 常见靶场资产关键词
    ASSET_KEYWORDS = {
        "database": ["mysql", "postgres", "mssql", "oracle", "db", "database", "mongo"],
        "domain_controller": ["dc", "domain", "ad", "ldap", "windows server", "域控"],
        "web": ["web", "http", "apache", "nginx", "iis", "tomcat"],
        "firewall": ["fw", "firewall", "asa", "pfsense", "iptables"],
        "dns": ["dns", "bind", "ns1", "ns2"],
        "mail": ["mail", "smtp", "postfix", "exchange", "pop", "imap"],
        "file": ["ftp", "sftp", "smb", "nfs", "file"],
    }

    def __init__(self, eve_client: EVEClient, kali_conn: Optional[Any] = None):
        """初始化联动模块

        :param eve_client: EVE-NG 客户端实例
        :param kali_conn: Kali 连接实例（预留，暂未使用）
        """
        self.eve = eve_client
        self.kali = kali_conn

    # -------------------------------------------------------------------------
    # 内部工具
    # -------------------------------------------------------------------------

    def _normalize_nodes(self, nodes_data: dict) -> List[dict]:
        """规范化节点数据"""
        nodes = nodes_data.get("data", {})
        if isinstance(nodes, dict):
            return list(nodes.values())
        return nodes if isinstance(nodes, list) else []

    def _normalize_networks(self, networks_data: dict) -> List[dict]:
        """规范化网络数据"""
        networks = networks_data.get("data", {})
        if isinstance(networks, dict):
            return list(networks.values())
        return networks if isinstance(networks, list) else []

    def _ip_in_subnet(self, ip: str, subnet_cidr: str) -> bool:
        """检查 IP 是否在指定子网内（简单实现）"""
        if not ip or "/" in subnet_cidr:
            return False
        try:
            parts = subnet_cidr.split("/")
            network = parts[0]
            prefix = int(parts[1]) if len(parts) > 1 else 32

            def ip_to_int(addr: str) -> int:
                octets = addr.split(".")
                return (int(octets[0]) << 24) + (int(octets[1]) << 16) + (int(octets[2]) << 8) + int(octets[3])

            ip_int = ip_to_int(ip)
            network_int = ip_to_int(network)
            mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
            return (ip_int & mask) == (network_int & mask)
        except Exception:
            return False

    def _is_management_ip(self, ip: str) -> bool:
        """判断是否为 EVE-NG 管理网络 IP"""
        if not ip:
            return False
        for net in self.MANAGEMENT_NETWORKS:
            if self._ip_in_subnet(ip, net):
                return True
        return False

    def _guess_node_role(self, node: dict) -> str:
        """根据节点名称和模板猜测节点角色"""
        name = node.get("name", "").lower()
        template = node.get("template", "").lower()
        console = node.get("console", "").lower()

        # Kali 机器
        if "kali" in name or "kal" in name:
            return "attacker"

        # 常见靶场资产模式
        for role, keywords in self.ASSET_KEYWORDS.items():
            for kw in keywords:
                if kw in name or kw in template:
                    return role

        # 网络设备类型
        if any(t in template for t in ["router", "iol", "linux", "ubuntu", "centos", "debian"]):
            if "router" in name or "rtr" in name:
                return "router"
            return "server"

        # 防火墙
        if any(t in template for t in ["asa", "firewall", "pfsense", "fw"]):
            return "firewall"

        # 交换机
        if any(t in template for t in ["switch", "ethernet"]):
            return "switch"

        # 网络类型
        if template in ["vpcs", "pc"]:
            return "host"

        return "unknown"

    def _parse_url_console(self, url: str) -> Tuple[str, int]:
        """从节点 url 字段解析 console IP 和端口

        url 格式示例: telnet://192.168.73.130:32771
        :returns: (console_ip, console_port)
        """
        if not url:
            return "", 0
        try:
            # 去除协议前缀
            addr = re.sub(r"^\w+://", "", url)
            if ":" in addr:
                ip_part, port_part = addr.rsplit(":", 1)
                return ip_part, int(port_part)
            return addr, 0
        except Exception:
            return "", 0

    def _get_node_interfaces(self, lab_path: str, node: dict) -> List[dict]:
        """获取节点的接口信息（从节点详情中提取）"""
        interfaces = []
        node_name = node.get("name", "")

        # 先尝试从节点数据直接获取
        url = node.get("url", "")
        if url:
            console_ip, console_port = self._parse_url_console(url)
            if console_ip:
                interfaces.append({
                    "name": "console",
                    "ip": console_ip,
                    "port": console_port,
                    "url": url,
                    "type": "console",
                })

        # 尝试从节点详情中获取接口
        try:
            node_detail = self.eve.client.api.get_node_by_name(lab_path, node_name)
            if node_detail:
                # 接口可能在 interfaces 或 ports 字段
                ifaces = node_detail.get("interfaces", {}) or node_detail.get("ports", {})
                if isinstance(ifaces, dict):
                    for iface_name, iface_data in ifaces.items():
                        if isinstance(iface_data, dict):
                            interfaces.append({
                                "name": iface_name,
                                "mac": iface_data.get("mac_address", "") or iface_data.get("mac", ""),
                                "ip": iface_data.get("ip_address", "") or iface_data.get("ip", ""),
                                "net_id": iface_data.get("network_id", "") or iface_data.get("net_id", ""),
                                "type": iface_data.get("type", "ethernet"),
                            })
                        else:
                            interfaces.append({
                                "name": str(iface_name),
                                "type": "ethernet",
                            })
                elif isinstance(ifaces, list):
                    for iface in ifaces:
                        interfaces.append({
                            "name": iface.get("name", ""),
                            "mac": iface.get("mac_address", ""),
                            "ip": iface.get("ip_address", ""),
                            "net_id": iface.get("network_id", ""),
                            "type": iface.get("type", "ethernet"),
                        })
        except Exception:
            pass

        return interfaces

    # -------------------------------------------------------------------------
    # 核心方法
    # -------------------------------------------------------------------------

    def get_lab_topology(self, lab_path: str) -> Dict[str, Any]:
        """获取实验拓扑（节点+网络+链路）

        :param lab_path: 实验路径，如 "/HW/tst.unl"
        :return: 包含 nodes、networks、links 的完整拓扑
        """
        try:
            # 并行获取节点和网络数据
            nodes_data = self.eve.client.api.list_nodes(lab_path)
            networks_data = self.eve.client.api.list_lab_networks(lab_path)

            nodes = self._normalize_nodes(nodes_data)
            networks = self._normalize_networks(networks_data)

            # 构建链路（从节点接口连接到网络）
            links = []
            for node in nodes:
                node_name = node.get("name", "")
                interfaces = self._get_node_interfaces(lab_path, node)
                for iface in interfaces:
                    net_id = iface.get("net_id", "")
                    if net_id:
                        # 找出网络名称
                        net_name = ""
                        for net in networks:
                            if str(net.get("id", "")) == str(net_id):
                                net_name = net.get("name", "")
                                break
                        if net_name:
                            links.append([node_name, iface.get("name", ""), net_name])

            return {
                "status": "success",
                "lab_path": lab_path,
                "nodes": nodes,
                "networks": networks,
                "links": links,
                "summary": {
                    "node_count": len(nodes),
                    "network_count": len(networks),
                    "link_count": len(links),
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_node_console_ips(self, lab_path: str) -> List[Dict[str, Any]]:
        """获取所有节点的 console IP 和端口

        EVE-NG 管理网络 IP 通常是 10.255.255.x 或 172.17.x.x
        Console 信息从节点的 url 字段提取，格式如：telnet://192.168.73.130:32771

        :param lab_path: 实验路径
        :return: 节点控制台信息列表
        """
        try:
            nodes_data = self.eve.client.api.list_nodes(lab_path)
            nodes = self._normalize_nodes(nodes_data)

            result = []
            for node in nodes:
                node_name = node.get("name", "")
                template = node.get("template", "")
                console_type = node.get("console", "telnet")
                url = node.get("url", "")

                # 从 url 字段解析 console IP 和端口
                console_ip, console_port = self._parse_url_console(url)

                # 状态
                status_map = {0: "stopped", 1: "starting", 2: "stopping", 3: "running", 4: "paused", 99: "error"}
                status = status_map.get(node.get("status", 0), "unknown")

                result.append({
                    "name": node_name,
                    "template": template,
                    "console_type": console_type,
                    "console_ip": console_ip,      # Console 连接 IP（从 url 解析）
                    "console_port": console_port, # Console 端口
                    "url": url,                     # 完整 url
                    "status": status,
                    "role": self._guess_node_role(node),
                    "is_mgmt_ip": self._is_management_ip(console_ip),
                    "node_id": str(node.get("id", "")),
                })

            return result
        except Exception as e:
            return [{"status": "error", "message": str(e)}]

    def find_gateway_nodes(self, lab_path: str) -> Dict[str, Any]:
        """找出边界节点（连接外部网络的节点）

        边界节点判断标准：
        - 连接了类型为 bridge/ovs/vxlan/nat/flat 的网络
        - 或者连接了非管理网段的网络

        :param lab_path: 实验路径
        :return: 边界节点分析结果
        """
        try:
            topo = self.get_lab_topology(lab_path)
            if topo.get("status") != "success":
                return topo

            nodes = topo.get("nodes", [])
            networks = topo.get("networks", [])
            links = topo.get("links", [])

            # 建立网络名称到网络详情的映射
            net_name_to_info = {}
            for net in networks:
                net_name_to_info[net.get("name", "")] = net

            # 找出外部网络（bridge/ovs/vxlan/nat/flat 等）
            external_networks = []
            internal_networks = []
            for net in networks:
                net_type = net.get("type", "").lower()
                net_name = net.get("name", "")
                if net_type in self.EXTERNAL_NETWORK_TYPES or "cloud" in net_type.lower() or "wan" in net_name.lower():
                    external_networks.append(net)
                else:
                    internal_networks.append(net)

            # 找出连接外部网络的节点
            gateway_nodes = []
            for link in links:
                if len(link) >= 3:
                    node_name, iface_name, net_name = link[0], link[1], link[2]
                    net_info = net_name_to_info.get(net_name, {})
                    net_type = net_info.get("type", "").lower()

                    if net_type in self.EXTERNAL_NETWORK_TYPES or "cloud" in net_type.lower():
                        # 检查节点是否已在列表中
                        existing = next((n for n in gateway_nodes if n["name"] == node_name), None)
                        if existing:
                            if net_name not in existing["external_networks"]:
                                existing["external_networks"].append(net_name)
                                existing["external_interfaces"].append(iface_name)
                        else:
                            # 获取节点管理 IP
                            node_detail = None
                            try:
                                node_detail = self.eve.client.api.get_node_by_name(lab_path, node_name)
                            except Exception:
                                pass

                            mgmt_ip = ""
                            if node_detail:
                                mgmt_ip = node_detail.get("ip_address", "")
                            else:
                                for n in nodes:
                                    if n.get("name") == node_name:
                                        mgmt_ip = n.get("ip_address", "")
                                        break

                            gateway_nodes.append({
                                "name": node_name,
                                "type": net_info.get("type", ""),
                                "role": self._guess_node_role({"name": node_name, "template": ""}),
                                "console_ip": mgmt_ip,
                                "external_networks": [net_name],
                                "external_interfaces": [iface_name],
                            })

            return {
                "status": "success",
                "gateway_nodes": gateway_nodes,
                "external_networks": external_networks,
                "internal_networks": internal_networks,
                "summary": f"{len(gateway_nodes)} gateway node(s), {len(external_networks)} external network(s), {len(internal_networks)} internal network(s)",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def export_topology_for_kali(self, lab_path: str, output_json: str) -> Dict[str, Any]:
        """导出拓扑为 Kali-ops 可读的 JSON

        :param lab_path: 实验路径
        :param output_json: 输出 JSON 文件路径
        :return: 导出结果
        """
        try:
            topo = self.get_lab_topology(lab_path)
            if topo.get("status") != "success":
                return topo

            nodes = topo.get("nodes", [])
            networks = topo.get("networks", [])
            links = topo.get("links", [])

            # 构建 Kali-ops 格式
            export_data = {
                "lab_name": os.path.splitext(os.path.basename(lab_path))[0],
                "lab_path": lab_path,
                "exported_at": datetime.now().isoformat(),
                "nodes": [],
                "networks": [],
                "links": [],
            }

            # 节点
            for node in nodes:
                node_name = node.get("name", "")
                node_detail = None
                try:
                    node_detail = self.eve.client.api.get_node_by_name(lab_path, node_name)
                except Exception:
                    pass

                # 优先从 url 解析 console IP
                url = node.get("url", "")
                console_ip, console_port = self._parse_url_console(url)
                mgmt_ip = node.get("ip_address", "") or console_ip

                interfaces = self._get_node_interfaces(lab_path, node)

                export_data["nodes"].append({
                    "name": node_name,
                    "ip": mgmt_ip,
                    "console_ip": console_ip,
                    "console_port": console_port,
                    "url": url,
                    "interfaces": interfaces,
                    "type": self._guess_node_role(node),
                    "template": node.get("template", ""),
                    "status": node.get("status", 0),
                    "console": node.get("console", "telnet"),
                    "node_id": str(node.get("id", "")),
                })

            # 网络
            for net in networks:
                export_data["networks"].append({
                    "name": net.get("name", ""),
                    "subnet": net.get("subnet", ""),          # 如果有子网信息
                    "type": net.get("type", "bridge"),
                    "id": net.get("id", ""),
                })

            # 链路
            for link in links:
                export_data["links"].append(link)

            # 写入文件
            output_dir = os.path.dirname(output_json)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return {
                "status": "success",
                "output_file": output_json,
                "nodes_exported": len(export_data["nodes"]),
                "networks_exported": len(export_data["networks"]),
                "links_exported": len(export_data["links"]),
                "data": export_data,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def build_pentest_topology(self, lab_path: str) -> Dict[str, Any]:
        """生成渗透测试视角的拓扑

        标识：
          - 入口点（可从互联网访问的节点）
          - 关键资产（数据库、域控等）
          - 潜在横移路径

        :param lab_path: 实验路径
        :return: 渗透测试视角拓扑
        """
        try:
            topo = self.get_lab_topology(lab_path)
            if topo.get("status") != "success":
                return topo

            nodes = topo.get("nodes", [])
            networks = topo.get("networks", [])
            links = topo.get("links", [])

            # 获取节点详情以获取管理 IP
            node_details = {}
            for node in nodes:
                name = node.get("name", "")
                try:
                    detail = self.eve.client.api.get_node_by_name(lab_path, name)
                    if detail:
                        node_details[name] = detail
                except Exception:
                    pass

            # 建立网络名称到节点的映射
            net_to_nodes: Dict[str, List[str]] = {}
            for link in links:
                if len(link) >= 3:
                    node_name, _, net_name = link[0], link[1], link[2]
                    if net_name not in net_to_nodes:
                        net_to_nodes[net_name] = []
                    if node_name not in net_to_nodes[net_name]:
                        net_to_nodes[net_name].append(node_name)

            # 分类节点
            entry_points = []      # 入口点（连接外部网络）
            key_assets = []        # 关键资产
            internal_nodes = []    # 内部节点
            kali_nodes = []        # Kali 攻击机

            for node in nodes:
                name = node.get("name", "")
                role = self._guess_node_role(node)
                detail = node_details.get(name, {})
                mgmt_ip = node.get("ip_address", "") or detail.get("ip_address", "")

                node_info = {
                    "name": name,
                    "role": role,
                    "console_ip": mgmt_ip,
                    "template": node.get("template", ""),
                    "connected_networks": net_to_nodes.get(name, []),
                }

                if role == "attacker" or "kali" in name.lower():
                    kali_nodes.append(node_info)
                elif role in ("database", "domain_controller", "firewall"):
                    key_assets.append(node_info)
                else:
                    # 检查是否连接外部网络
                    connected_nets = net_to_nodes.get(name, [])
                    is_external = False
                    for net in networks:
                        if net.get("name", "") in connected_nets:
                            net_type = net.get("type", "").lower()
                            if net_type in self.EXTERNAL_NETWORK_TYPES or "cloud" in net_type:
                                is_external = True
                                break

                    if is_external:
                        entry_points.append(node_info)
                    else:
                        internal_nodes.append(node_info)

            # 构建横移路径图（网络连通性）
            lateral_paths = []
            for net_name, node_list in net_to_nodes.items():
                if len(node_list) > 1:
                    for i, src in enumerate(node_list):
                        for dst in node_list[i + 1:]:
                            lateral_paths.append({
                                "from": src,
                                "to": dst,
                                "via_network": net_name,
                            })

            # 攻击路径分析（从 Kali 到关键资产的可能路径）
            attack_paths = []
            for kali in kali_nodes:
                for asset in key_assets:
                    # 简单 BFS 找路径（这里用贪心近似）
                    path = self._find_attack_path(kali["name"], asset["name"], net_to_nodes)
                    if path:
                        attack_paths.append({
                            "from": kali["name"],
                            "to": asset["name"],
                            "path": path,
                        })

            return {
                "status": "success",
                "lab_path": lab_path,
                "lab_name": os.path.splitext(os.path.basename(lab_path))[0],
                "analysis": {
                    "entry_points": entry_points,
                    "key_assets": key_assets,
                    "internal_nodes": internal_nodes,
                    "kali_nodes": kali_nodes,
                    "lateral_movement_paths": lateral_paths,
                    "attack_paths": attack_paths,
                },
                "summary": {
                    "entry_point_count": len(entry_points),
                    "key_asset_count": len(key_assets),
                    "internal_node_count": len(internal_nodes),
                    "kali_count": len(kali_nodes),
                    "lateral_path_count": len(lateral_paths),
                    "attack_path_count": len(attack_paths),
                },
                "recommendations": self._generate_recommendations(entry_points, key_assets, kali_nodes),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _find_attack_path(
        self,
        src: str,
        dst: str,
        net_to_nodes: Dict[str, List[str]],
    ) -> List[str]:
        """简单贪心搜索从 src 到 dst 的路径（经过网络）"""
        if src == dst:
            return [src]

        # 构建节点到网络到节点的邻接表
        node_neighbors: Dict[str, List[Tuple[str, str]]] = {}
        for net_name, node_list in net_to_nodes.items():
            for node in node_list:
                if node not in node_neighbors:
                    node_neighbors[node] = []
                for other in node_list:
                    if other != node:
                        node_neighbors[node].append((other, net_name))

        # BFS
        visited = {src}
        queue = [(src, [src])]

        while queue:
            current, path = queue.pop(0)
            for neighbor, via_net in node_neighbors.get(current, []):
                if neighbor == dst:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def _generate_recommendations(
        self,
        entry_points: List[Dict],
        key_assets: List[Dict],
        kali_nodes: List[Dict],
    ) -> List[str]:
        """生成渗透测试建议"""
        recommendations = []

        if not kali_nodes:
            recommendations.append("⚠️ 未在靶场中发现 Kali 攻击机，建议添加 Kali 节点作为攻击源")

        if not entry_points:
            recommendations.append("⚠️ 未发现边界入口点，请检查网络类型配置")
        else:
            recommendations.append(f"✅ 发现 {len(entry_points)} 个边界入口点，可作为渗透入口")
            for ep in entry_points[:3]:
                recommendations.append(f"  → {ep['name']} (IP: {ep.get('console_ip', 'N/A')}, Role: {ep.get('role', 'unknown')})")

        if key_assets:
            recommendations.append(f"🎯 发现 {len(key_assets)} 个关键资产，优先目标：")
            for asset in key_assets[:3]:
                recommendations.append(f"  → {asset['name']} (Role: {asset.get('role', 'unknown')}, IP: {asset.get('console_ip', 'N/A')})")

        if entry_points and key_assets:
            recommendations.append("📋 建议攻击路径：边界入口 → 内部网络 → 关键资产")

        return recommendations

    def __repr__(self) -> str:
        return f"Kali联动(eve={self.eve}, kali={self.kali})"
