# -*- coding: utf-8 -*-
"""用正确接口名重建OSPF实验"""
import sys
import time
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController
import json

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
print("Connected!")

builder = LabBuilder(client)
controller = LabController(client)

lab_name = "OSPF_Routing_Lab"
lab_path = f"/{lab_name}.unl"

# 删除旧 lab
if builder.lab_exists(lab_path):
    print(f"删除旧 lab: {lab_path}")
    builder.delete_lab(lab_path)
    time.sleep(2)

# 用 build_from_yaml 构建（用修正后的接口名）
print("\n=== 从 YAML 构建拓扑 ===")
result = builder.build_from_yaml(
    r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\templates\ospf_lab.yaml'
)
print(f"Lab path: {result.get('lab_path')}")
print(f"Lab created: {result.get('lab_created')}")

print("\n--- 网络 ---")
for n in result.get('networks', []):
    print(f"  {n['name']}: {n['result'].get('status')} - {n['result'].get('message', '')[:80]}")

print("\n--- 节点 ---")
for n in result.get('nodes', []):
    print(f"  {n['name']}: {n['result'].get('status')} - {n['result'].get('message', '')[:80]}")

print("\n--- 链路 ---")
for l in result.get('links', []):
    r = l['result']
    status = r.get('status') if isinstance(r, dict) else r
    msg = r.get('message', '')[:80] if isinstance(r, dict) else str(r)[:80]
    print(f"  {l['link']}: {status} - {msg}")

lab_path_out = result.get('lab_path', '')

# 验证接口连接
print("\n=== 验证接口连接 ===")
for node_name in ["R1", "R2", "R3"]:
    node_info = client.client.api.get_node_by_name(lab_path_out, node_name)
    if node_info:
        ifaces = client.client.api.get_node_interfaces(lab_path_out, node_info['id'])
        print(f"{node_name}:")
        for eth in ifaces.get('data', {}).get('ethernet', []):
            print(f"  {eth['name']} -> network_id={eth['network_id']}")

# 启动所有节点
print("\n=== 启动所有节点 ===")
start_result = controller.start_all_nodes(lab_path_out)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message', '')}")

# 等待节点启动
print("\n等待10秒让节点完全启动...")
time.sleep(10)

# 检查状态
print("\n=== 节点最终状态 ===")
nodes = client.client.api.list_nodes(lab_path_out)
for nid, ndata in nodes.get('data', {}).items():
    status_map = {0: 'stopped', 1: 'starting', 2: 'stopping', 3: 'running', 4: 'paused', 99: 'error'}
    status = status_map.get(ndata.get('status'), ndata.get('status'))
    print(f"  {ndata['name']}: status={status} url={ndata.get('url','')}")

client.disconnect()
print("\n完成!")
