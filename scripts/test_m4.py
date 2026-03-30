"""
EVE-NG M4 测试脚本：配置注入与快照管理
测试对象：/HW/tst.unl
"""

import os
import sys

# Fix Windows console encoding
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import EVEClient
from config_manager import ConfigManager


def print_section(title: str):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {title}")
    print(sep)


def main():
    print_section("M4 Test - EVE-NG Config Manager")

    # 1. 连接
    client = EVEClient.from_config()
    client.connect()
    print(f"[OK] Connected: {client}")

    mgr = ConfigManager(client)
    lab_path = "/HW/tst.unl"

    try:
        # Test 1: 列出节点配置摘要
        print_section("Test 1: list_node_configs_summary")
        summary = mgr.list_node_configs_summary(lab_path)
        print(f"Node count: {len(summary)}")
        for n in summary:
            has_config = "✓" if n.get("has_custom_config") else "✗"
            print(
                f"  [{has_config}] {n.get('node_name')} | template={n.get('template')} | "
                f"console={n.get('console')} | ip={n.get('ip_address', 'N/A')}"
            )

        if not summary:
            print("  (No nodes found or failed to query)")
        else:
            first_node = summary[0]["node_name"]
            print(f"\nUsing first node: {first_node}")

            # Test 2: 获取节点配置
            print_section(f"Test 2: get_config - {first_node}")
            config_result = mgr.get_config(lab_path, first_node)
            if config_result.get("status") == "success":
                config_text = config_result.get("config", "")
                print(f"  Status: success")
                print(f"  Config length: {len(config_text)} chars")
                if config_text:
                    print(f"  Config preview (first 300 chars):")
                    preview = config_text[:300].replace("\n", "\\n")
                    print(f"    {preview}")
                else:
                    print("  Config is empty (node uses default image config)")
            else:
                print(f"  Error: {config_result.get('message')}")

            # Test 3: 上传一个简单配置
            print_section(f"Test 3: upload_config - {first_node}")
            test_config = """!
! Test configuration uploaded via EVE-NG API
! Date: 2026-03-25
!
hostname TEST-ROUTER
!
interface Ethernet0/0
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
line con 0
 logging synchronous
 login local
!
end
"""
            upload_result = mgr.upload_config(lab_path, first_node, test_config)
            print(f"  Result: {upload_result.get('status')}")
            print(f"  Response: {upload_result.get('response', upload_result)}")

            # Test 4: 启用启动配置
            print_section(f"Test 4: enable_startup_config - {first_node}")
            enable_result = mgr.enable_startup_config(lab_path, first_node)
            print(f"  Result: {enable_result.get('status')}")
            print(f"  Response: {enable_result.get('response', enable_result)}")

            # Test 5: 导出节点配置到文件
            print_section(f"Test 5: export_node_config - {first_node}")
            export_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
            os.makedirs(export_dir, exist_ok=True)
            export_result = mgr.export_node_config(
                lab_path, first_node,
                os.path.join(export_dir, f"config_{first_node}.cfg")
            )
            if export_result.get("status") == "success":
                print(f"  File: {export_result.get('file_path')}")
                print(f"  Bytes: {export_result.get('bytes_written')}")
            else:
                print(f"  Result: {export_result}")

        # Test 6: 导出实验为 .unl
        print_section("Test 6: export_lab")
        export_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
        export_result = mgr.export_lab(lab_path, export_dir)
        print(f"  Status: {export_result.get('status')}")
        if export_result.get("status") == "success":
            print(f"  Output file: {export_result.get('output_file')}")
            print(f"  Full path: {export_result.get('full_path')}")
            # Verify file exists
            full_path = export_result.get("full_path")
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"  File size: {size:,} bytes")
        else:
            print(f"  Error: {export_result.get('message')}")

        print_section("M4 Tests Completed")

    finally:
        client.disconnect()
        print("\n[OK] Disconnected")


if __name__ == "__main__":
    main()
