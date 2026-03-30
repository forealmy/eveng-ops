"""
EVE-NG M3 测试脚本：实验环境控制
测试对象：/HW/tst.unl
"""
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import json
import sys
import time

# Fix Windows console encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from client import EVEClient
from lab_controller import LabController


def print_section(title: str):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


def main():
    # 1. 连接 EVE-NG
    print_section("M3 Test - EVE-NG Lab Controller")
    client = EVEClient.from_config()
    client.connect()
    print(f"[OK] Connected: {client}")

    ctrl = LabController(client)
    lab_path = "/HW/tst.unl"

    try:
        # Test 1: 列出所有节点状态
        print_section("Test 1: list_node_status")
        nodes = ctrl.list_node_status(lab_path)
        print(f"Node count: {len(nodes)}")
        for n in nodes:
            print(f"  [{n.get('status_text', 'N/A')}] {n.get('name')} | "
                  f"template={n.get('template')} | ip={n.get('ip_address', 'N/A')}")

        if not nodes:
            print("  (No nodes or failed to get nodes)")
        else:
            test_node = nodes[0]["name"]

            # Test 2: 获取整体实验状态
            print_section("Test 2: get_lab_status")
            lab_status = ctrl.get_lab_status(lab_path)
            print(f"  lab_path: {lab_status.get('lab_path')}")
            print(f"  summary: {lab_status.get('node_summary')}")
            print(f"  running={lab_status.get('running_nodes')}, "
                  f"stopped={lab_status.get('stopped_nodes')}, "
                  f"total={lab_status.get('total_nodes')}")

            # Test 3: 启动节点
            print_section(f"Test 3: start_node - {test_node}")
            start_resp = ctrl.start_node(lab_path, test_node)
            print(f"  Response: {json.dumps(start_resp, ensure_ascii=False)}")

            # Test 4: 获取节点状态
            print_section(f"Test 4: get_node_status - {test_node}")
            time.sleep(2)
            node_status = ctrl.get_node_status(lab_path, test_node)
            if node_status.get("status") == "success":
                print(f"  status: {node_status.get('run_status')} ({node_status.get('run_status_text')})")
                print(f"  node_id: {node_status.get('node_id')}")
            else:
                print(f"  Response: {json.dumps(node_status, ensure_ascii=False)}")

            # Test 5: 停止节点
            print_section(f"Test 5: stop_node - {test_node}")
            stop_resp = ctrl.stop_node(lab_path, test_node)
            print(f"  Response: {json.dumps(stop_resp, ensure_ascii=False)}")

            # Test 6: 验证停止后状态
            time.sleep(2)
            node_status_after = ctrl.get_node_status(lab_path, test_node)
            if node_status_after.get("status") == "success":
                print(f"  After stop: {node_status_after.get('run_status')} ({node_status_after.get('run_status_text')})")

            print_section("All Tests Completed")

    finally:
        client.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()
