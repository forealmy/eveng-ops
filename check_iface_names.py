# -*- coding: utf-8 -*-
"""检查节点接口名称"""
import sys
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
import json

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()

lab_path = "/OSPF_Routing_Lab.unl"

# 查看节点已有的接口信息
print("=== 获取节点接口 ===")
for node_name in ["R1", "R2", "R3"]:
    node_info = client.client.api.get_node_by_name(lab_path, node_name)
    if node_info:
        node_id = node_info.get('id')
        print(f"\n{node_name} (id={node_id}):")
        try:
            ifaces = client.client.api.get_node_interfaces(lab_path, node_id)
            print(json.dumps(ifaces, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"  get_node_interfaces error: {e}")
    else:
        print(f"{node_name}: not found")

# 查看已知的华为AR接口命名规则
print("\n=== 检查华为AR1K模板 ===")
templates = client.client.api.list_node_templates()
for t in templates.get('data', []):
    if 'huawei' in t.get('name', '').lower() or 'ar' in t.get('name', '').lower():
        print(f"  {t}")

client.disconnect()
