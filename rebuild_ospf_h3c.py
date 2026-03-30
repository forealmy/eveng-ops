# -*- coding: utf-8 -*-
"""OSPF实验 - 使用H3C vSR1000路由器重建"""
import sys
import time
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
print("Connected!")

builder = LabBuilder(client)
controller = LabController(client)

lab_name = "OSPF_H3C_Lab"
lab_path = f"/{lab_name}.unl"

# 删除旧 lab
if builder.lab_exists(lab_path):
    print(f"[1] 删除旧 lab: {lab_path}")
    builder.delete_lab(lab_path)
    time.sleep(3)

# 创建 lab
print(f"[2] 创建 lab: {lab_name}")
builder.create_lab(lab_name=lab_name, lab_path="/", author="admin", description="H3C vSR OSPF路由实验")
time.sleep(1)

# 创建3个 H3C vSR1000 网络（bridge）
print("[3] 创建网络")
for net_name in ["Net1", "Net2", "Net3"]:
    r = client.client.api.add_lab_network(lab_path, "bridge", 1, name=net_name)
    print(f"  {net_name}: {r.get('status')}")
time.sleep(2)

# 创建 3 个 H3C vSR1000 路由器
print("[4] 创建 H3C vSR1000 路由器节点")
node_ids = {}
for node_name in ["R1", "R2", "R3"]:
    r = client.client.api.add_node(lab_path, "h3cvsr1k", 0,
                                   name=node_name, node_type="qemu",
                                   console="telnet", ram=1024, ethernet=3)
    print(f"  {node_name}: {r.get('status')}")
    time.sleep(1)
    ni = client.client.api.get_node_by_name(lab_path, node_name)
    if ni:
        node_ids[node_name] = ni['id']
        ifaces = client.client.api.get_node_interfaces(lab_path, ni['id'])
        eths = [e['name'] for e in ifaces.get('data',{}).get('ethernet',[])]
        print(f"    -> id={ni['id']} 接口={eths}")

# 启动所有节点
print("[5] 启动所有节点")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message')}")

# 等待节点启动
print("[6] 等待15秒节点启动...")
for i in range(15):
    time.sleep(1)
    nodes = client.client.api.list_nodes(lab_path)
    running = {nid: ndata for nid, ndata in nodes.get('data',{}).items() if ndata.get('status') == 3}
    stopped = {nid: ndata for nid, ndata in nodes.get('data',{}).items() if ndata.get('status') != 3}
    print(f"  {i+1}秒: {len(running)} running, {len(stopped)} stopped")
    if len(running) == 3:
        print("  所有节点已启动!")
        break

# 连接链路
print("[7] 连接链路（H3C GE接口格式）")
# H3C vSR 接口: GE1/0, GE2/0, GE3/0 (第一个GE是 GE1/0 不是 GE0/0!)
links = [
    ("R1", "GE1/0", "Net1"),
    ("R1", "GE2/0", "Net2"),
    ("R2", "GE1/0", "Net2"),
    ("R2", "GE2/0", "Net3"),
    ("R3", "GE1/0", "Net3"),
]
for node, iface, net in links:
    try:
        r = client.client.api.connect_node_to_cloud(lab_path, node, iface, net)
        status = r.get('status')
        msg = r.get('message', '')[:60]
        print(f"  {node}[{iface}] -> {net}: {status} {msg}")
    except Exception as e:
        print(f"  {node}[{iface}] -> {net}: ERROR {e}")
    time.sleep(1)

# 最终验证
print("\n[8] 最终状态")
nodes = client.client.api.list_nodes(lab_path)
status_map = {0:'stopped',1:'starting',2:'stopping',3:'running',4:'paused',99:'error'}
for nid, ndata in nodes.get('data', {}).items():
    s = status_map.get(ndata.get('status'), ndata.get('status'))
    ifaces = client.client.api.get_node_interfaces(lab_path, nid)
    eths = [f"{e['name']}->nid{e['network_id']}" for e in ifaces.get('data',{}).get('ethernet',[])]
    print(f"  {ndata['name']}: {s} | {', '.join(eths)}")

nets = client.client.api.list_lab_networks(lab_path)
for nid, ndata in nets.get('data', {}).items():
    print(f"  网络 {ndata['name']}: count={ndata['count']}")

client.disconnect()
print("\n完成!")
