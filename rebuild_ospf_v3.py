# -*- coding: utf-8 -*-
"""OSPF实验 - 分步构建：先起节点再连线"""
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
    print(f"[1] 删除旧 lab")
    builder.delete_lab(lab_path)
    time.sleep(3)

# 创建 lab
print(f"[2] 创建 lab")
builder.create_lab(lab_name=lab_name, lab_path="/", author="admin", description="OSPF路由实验")
time.sleep(1)

# 创建网络
print("[3] 创建网络")
for net_name in ["Net1", "Net2", "Net3"]:
    r = client.client.api.add_lab_network(lab_path, "bridge", 1, name=net_name)
    print(f"  {net_name}: {r.get('status')}")
time.sleep(2)  # 等待网络就绪

# 创建节点（不起步）
print("[4] 创建节点")
for node_name in ["R1", "R2", "R3"]:
    r = client.client.api.add_node(lab_path, "huaweiar1k", 0,
                                   name=node_name, node_type="qemu",
                                   console="telnet", ram=512, ethernet=3)
    print(f"  {node_name}: {r.get('status')}")
time.sleep(2)

# 验证节点接口名
print("[5] 验证接口名称")
for node_name in ["R1", "R2", "R3"]:
    ni = client.client.api.get_node_by_name(lab_path, node_name)
    ifaces = client.client.api.get_node_interfaces(lab_path, ni['id'])
    print(f"  {node_name}: {[e['name'] for e in ifaces.get('data',{}).get('ethernet',[])]}")

# 启动所有节点
print("[6] 启动所有节点")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message')}")

# 等待节点完全启动
print("[7] 等待15秒节点启动...")
for i in range(15):
    time.sleep(1)
    nodes = client.client.api.list_nodes(lab_path)
    running = sum(1 for n in nodes.get('data',{}).values() if n.get('status') == 3)
    print(f"  {i+1}秒: {running}/3 running")
    if running == 3:
        print("  所有节点已启动!")
        break

# 节点启动后，再连接链路
print("[8] 连接链路（G0/0/0格式）")
links = [
    ("R1", "G0/0/0", "Net1"),
    ("R1", "G0/0/1", "Net2"),
    ("R2", "G0/0/0", "Net2"),
    ("R2", "G0/0/1", "Net3"),
    ("R3", "G0/0/0", "Net3"),
]
for node, iface, net in links:
    try:
        r = client.client.api.connect_node_to_cloud(lab_path, node, iface, net)
        print(f"  {node}[{iface}] -> {net}: {r.get('status')} {r.get('message','')[:60]}")
    except Exception as e:
        print(f"  {node}[{iface}] -> {net}: ERROR {e}")
    time.sleep(1)

# 最终验证
print("\n[9] 最终状态")
nodes = client.client.api.list_nodes(lab_path)
for nid, ndata in nodes.get('data', {}).items():
    status_map = {0:'stopped',1:'starting',2:'stopping',3:'running',4:'paused',99:'error'}
    s = status_map.get(ndata.get('status'), ndata.get('status'))
    ifaces = client.client.api.get_node_interfaces(lab_path, nid)
    nets = [f"{e['name']}->nid{e['network_id']}" for e in ifaces.get('data',{}).get('ethernet',[])]
    print(f"  {ndata['name']}: {s} | {', '.join(nets)}")

nets = client.client.api.list_lab_networks(lab_path)
print(f"  网络: {list(nets.get('data',{}).values())}")

client.disconnect()
print("\n完成!")
