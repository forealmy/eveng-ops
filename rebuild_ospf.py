# -*- coding: utf-8 -*-
"""重新构建OSPF实验，带详细调试信息"""
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
print(f"\n删除旧 lab: {lab_path}")
if builder.lab_exists(lab_path):
    resp = builder.delete_lab(lab_path)
    print(f"删除结果: {resp}")
    time.sleep(2)

# 重新创建 lab
print(f"\n创建 lab...")
create_resp = builder.create_lab(lab_name=lab_name, lab_path="/", author="admin", description="OSPF路由实验")
print(f"创建结果: {json.dumps(create_resp, indent=2, ensure_ascii=False)}")
time.sleep(1)

# 创建网络
print("\n=== 创建3个网络 ===")
networks_def = ["Net1", "Net2", "Net3"]
net_ids = {}
for net_name in networks_def:
    resp = client.client.api.add_lab_network(
        path=lab_path,
        name=net_name,
        network_type="bridge",
        visibility=1
    )
    print(f"  {net_name}: {resp}")
    time.sleep(0.5)
    # 查询网络详情
    net_info = client.client.api.get_lab_network_by_name(lab_path, net_name)
    net_id = net_info.get('id') if net_info else None
    net_ids[net_name] = net_id
    print(f"    -> net_id={net_id}")

# 验证网络已创建
print("\n=== 验证网络列表 ===")
nets = client.client.api.list_lab_networks(lab_path)
print(json.dumps(nets, indent=2, ensure_ascii=False))

# 创建节点
print("\n=== 创建3个节点 ===")
nodes_def = [
    {"name": "R1", "template": "huaweiar1k", "ram": 512, "ethernet": 3},
    {"name": "R2", "template": "huaweiar1k", "ram": 512, "ethernet": 3},
    {"name": "R3", "template": "huaweiar1k", "ram": 512, "ethernet": 3},
]
node_ids = {}
for nd in nodes_def:
    resp = client.client.api.add_node(
        path=lab_path,
        name=nd["name"],
        template=nd["template"],
        ram=nd["ram"],
        ethernet=nd["ethernet"],
        node_type="qemu",
        console="telnet",
        delay=0
    )
    print(f"  {nd['name']}: {resp}")
    time.sleep(0.5)
    node_info = client.client.api.get_node_by_name(lab_path, nd["name"])
    nid = node_info.get('id') if node_info else None
    node_ids[nd['name']] = nid
    print(f"    -> node_id={nid}")

# 验证节点已创建
print("\n=== 验证节点列表 ===")
nodes = client.client.api.list_nodes(lab_path)
print(json.dumps(nodes, indent=2, ensure_ascii=False))

# 连接链路 - 用精确参数
print("\n=== 连接链路 ===")
links = [
    ("R1", "eth0", "Net1"),
    ("R1", "eth1", "Net2"),
    ("R2", "eth0", "Net2"),
    ("R2", "eth1", "Net3"),
    ("R3", "eth0", "Net3"),
]

for node_name, iface, net_name in links:
    print(f"  {node_name}[{iface}] -> {net_name}")
    try:
        resp = client.client.api.connect_node_to_cloud(
            path=lab_path,
            src=node_name,
            src_label=iface,
            dst=net_name
        )
        print(f"    -> {resp}")
    except Exception as e:
        print(f"    -> ERROR: {type(e).__name__}: {e}")
    time.sleep(0.5)

# 再次验证网络（看count是否变化）
print("\n=== 验证网络连接后 ===")
nets = client.client.api.list_lab_networks(lab_path)
print(json.dumps(nets, indent=2, ensure_ascii=False))

# 启动所有节点
print("\n=== 启动所有节点 ===")
start_result = controller.start_all_nodes(lab_path)
print(json.dumps(start_result, indent=2, ensure_ascii=False))

# 等待几秒后查状态
time.sleep(5)
print("\n=== 5秒后节点状态 ===")
nodes = client.client.api.list_nodes(lab_path)
for nid, ndata in nodes.get('data', {}).items():
    print(f"  {ndata['name']}: status={ndata['status']} url={ndata.get('url','')}")

client.disconnect()
print("\n完成!")
