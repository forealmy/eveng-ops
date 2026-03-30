# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
import json

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()

# 列出所有 H3C 模板
templates = client.client.api.list_node_templates()
print("=== H3C 模板列表 ===")
for key, val in templates.get('data', {}).items():
    if 'h3c' in key.lower():
        print(f"  {key}: {val}")

# 查看当前 OSPF 实验状态
print("\n=== 当前 OSPF 实验状态 ===")
try:
    nodes = client.client.api.list_nodes('/OSPF_Routing_Lab.unl')
    for nid, n in nodes.get('data', {}).items():
        print(f"  {n['name']}: status={n['status']} url={n.get('url','')}")
        ifaces = client.client.api.get_node_interfaces('/OSPF_Routing_Lab.unl', nid)
        eths = [e['name'] for e in ifaces.get('data',{}).get('ethernet',[])]
        print(f"    接口: {eths}")
except Exception as e:
    print(f"  实验不存在或无法访问: {e}")

client.disconnect()
