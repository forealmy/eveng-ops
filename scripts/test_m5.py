"""
EVE-NG M5 测试脚本：Kali-ops 联动
测试对象：/HW/tst.unl
"""

import json
import os
import sys

# Fix Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import EVEClient
from kali联动 import Kali联动


def print_section(title: str):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


def main():
    print_section("M5 Test - EVE-NG Kali-ops 联动")

    # 1. 连接
    client = EVEClient.from_config()
    client.connect()
    print(f"[OK] Connected: {client}")

    kali = Kali联动(client)
    lab_path = "/HW/tst.unl"

    # 确认 reports 目录
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    try:
        # Test 1: 获取拓扑
        print_section("Test 1: get_lab_topology")
        topo = kali.get_lab_topology(lab_path)
        if topo.get("status") == "success":
            print(f"  Lab: {lab_path}")
            print(f"  节点数: {topo['summary']['node_count']}")
            print(f"  网络数: {topo['summary']['network_count']}")
            print(f"  链路数: {topo['summary']['link_count']}")
            print("\n  节点列表:")
            for n in topo.get("nodes", []):
                print(f"    - {n.get('name')} | template={n.get('template')} | url={n.get('url', 'N/A')} | status={n.get('status')}")
            print("\n  网络列表:")
            for net in topo.get("networks", []):
                print(f"    - {net.get('name')} | type={net.get('type')} | id={net.get('id')} | count={net.get('count', 'N/A')}")
            print("\n  链路列表:")
            for link in topo.get("links", []):
                print(f"    - {link}")
        else:
            print(f"  Error: {topo.get('message')}")

        # Test 2: 获取节点 console IP
        print_section("Test 2: get_node_console_ips")
        console_ips = kali.get_node_console_ips(lab_path)
        if console_ips and console_ips[0].get("status") != "error":
            print(f"  总节点数: {len(console_ips)}")
            print("\n  节点控制台信息:")
            for node in console_ips:
                is_mgmt = "✓ 管理网" if node.get("is_mgmt_ip") else "  "
                print(f"    [{is_mgmt}] {node.get('name'):20s} | console_ip={node.get('console_ip', 'N/A'):18s} | port={node.get('console_port', 'N/A'):>5} | console={node.get('console_type'):8s} | role={node.get('role'):15s} | status={node.get('status')}")
        else:
            err_msg = console_ips[0].get('message', str(console_ips)) if isinstance(console_ips, list) else str(console_ips)
            print(f"  Error: {err_msg}")

        # Test 3: 查找边界节点
        print_section("Test 3: find_gateway_nodes")
        gateways = kali.find_gateway_nodes(lab_path)
        if gateways.get("status") == "success":
            print(f"  {gateways.get('summary')}")
            print(f"\n  边界节点 ({len(gateways.get('gateway_nodes', []))}):")
            for gw in gateways.get("gateway_nodes", []):
                print(f"    → {gw.get('name')} | console_ip={gw.get('console_ip', 'N/A')} | role={gw.get('role')} | external_net={gw.get('external_networks')}")
            print(f"\n  外部网络 ({len(gateways.get('external_networks', []))}):")
            for net in gateways.get("external_networks", []):
                print(f"    - {net.get('name')} | type={net.get('type')}")
            print(f"\n  内部网络 ({len(gateways.get('internal_networks', []))}):")
            for net in gateways.get("internal_networks", []):
                print(f"    - {net.get('name')} | type={net.get('type')}")
        else:
            print(f"  Error: {gateways.get('message')}")

        # Test 4: 导出拓扑为 Kali-ops JSON
        print_section("Test 4: export_topology_for_kali")
        output_json = os.path.join(reports_dir, "tst_topology_for_kali.json")
        export_result = kali.export_topology_for_kali(lab_path, output_json)
        if export_result.get("status") == "success":
            print(f"  ✅ 导出成功: {output_json}")
            print(f"  节点: {export_result.get('nodes_exported')}")
            print(f"  网络: {export_result.get('networks_exported')}")
            print(f"  链路: {export_result.get('links_exported')}")
            # 显示 JSON 内容
            data = export_result.get("data", {})
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            print(f"\n  JSON 内容预览 (前 2000 字符):")
            print(json_str[:2000])
        else:
            print(f"  Error: {export_result.get('message')}")

        # Test 5: 生成渗透测试视角拓扑
        print_section("Test 5: build_pentest_topology")
        pentest = kali.build_pentest_topology(lab_path)
        if pentest.get("status") == "success":
            summary = pentest.get("summary", {})
            print(f"  入口点: {summary.get('entry_point_count', 0)}")
            print(f"  关键资产: {summary.get('key_asset_count', 0)}")
            print(f"  内部节点: {summary.get('internal_node_count', 0)}")
            print(f"  Kali节点: {summary.get('kali_count', 0)}")
            print(f"  横移路径: {summary.get('lateral_path_count', 0)}")
            print(f"  攻击路径: {summary.get('attack_path_count', 0)}")

            analysis = pentest.get("analysis", {})
            if analysis.get("entry_points"):
                print("\n  入口点详情:")
                for ep in analysis["entry_points"]:
                    print(f"    → {ep['name']} | ip={ep.get('console_ip', 'N/A')} | role={ep.get('role')}")
            if analysis.get("key_assets"):
                print("\n  关键资产:")
                for asset in analysis["key_assets"]:
                    print(f"    🎯 {asset['name']} | ip={asset.get('console_ip', 'N/A')} | role={asset.get('role')}")
            if analysis.get("kali_nodes"):
                print("\n  Kali 节点:")
                for k in analysis["kali_nodes"]:
                    print(f"    🐧 {k['name']} | ip={k.get('console_ip', 'N/A')} | role={k.get('role')}")
            if analysis.get("attack_paths"):
                print("\n  攻击路径:")
                for ap in analysis["attack_paths"][:5]:
                    print(f"    {' → '.join(ap['path'])}")

            print("\n  建议:")
            for rec in pentest.get("recommendations", []):
                print(f"    {rec}")
        else:
            print(f"  Error: {pentest.get('message')}")

        print_section("M5 Tests Completed")

    finally:
        client.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()
