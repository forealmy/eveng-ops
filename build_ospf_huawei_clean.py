# -*- coding: utf-8 -*-
"""华为AR1K OSPF实验 - 最终版"""
import sys, time
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
builder = LabBuilder(client)
controller = LabController(client)

lab_name = "Huawei_OSPF"
lab_path = f"/{lab_name}.unl"

print("[1] 清理旧lab")
for old in ["Huawei_OSPF", "Huawei_Test"]:
    if builder.lab_exists(f"/{old}.unl"):
        builder.delete_lab(f"/{old}.unl")
        print(f"  删除 {old}")
time.sleep(2)

print("[2] 创建lab")
builder.create_lab(lab_name=lab_name, lab_path="/", author="admin", description="华为AR1K OSPF单区域实验")
time.sleep(1)

print("[3] 创建网络")
for net_name in ["Net1", "Net2", "Net3"]:
    r = client.client.api.add_lab_network(lab_path, "bridge", 1, name=net_name)
    print(f"  {net_name}: {r.get('status')}")
time.sleep(2)

print("[4] 创建3个华为AR1K节点")
for node_name in ["R1", "R2", "R3"]:
    r = client.client.api.add_node(lab_path, "huaweiar1k", 0,
        name=node_name, node_type="qemu", console="telnet",
        ram=2048, ethernet=8)
    print(f"  {node_name}: {r.get('status')}")
    time.sleep(1)

# 验证接口名
print("\n[5] 验证接口名称")
for node_name in ["R1", "R2", "R3"]:
    ni = builder.get_node_by_name(lab_path, node_name)
    ifaces = client.client.api.get_node_interfaces(lab_path, ni['id'])
    eths = [e['name'] for e in ifaces.get('data',{}).get('ethernet',[])]
    print(f"  {node_name}: {eths}")

print("\n[6] 启动所有节点")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message')}")

print("\n[7] 等待20秒...")
time.sleep(20)

print("\n[8] 连接链路（华为接口G0/0/X）")
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
        print(f"  {node}[{iface}]->{net}: {r.get('status')} {r.get('message','')[:60]}")
    except Exception as e:
        print(f"  {node}[{iface}]->{net}: ERROR {e}")
    time.sleep(0.5)

print("\n[9] 最终状态")
nodes = client.client.api.list_nodes(lab_path)
status_map = {0:'stopped',1:'starting',2:'stopping',3:'running',4:'paused',99:'error'}
for nid, n in nodes.get('data', {}).items():
    s = status_map.get(n.get('status'), n.get('status'))
    ifaces = client.client.api.get_node_interfaces(lab_path, nid)
    eths = [f"{e['name']}->nid{e['network_id']}" for e in ifaces.get('data',{}).get('ethernet',[])]
    print(f"  {n['name']}: {s} | {', '.join(eths)}")

nets = client.client.api.list_lab_networks(lab_path)
for nid, n in nets.get('data', {}).items():
    print(f"  网络 {n['name']}: count={n['count']}")

print("\nConsole信息:")
for nid, n in nodes.get('data', {}).items():
    print(f"  {n['name']}: telnet://192.168.73.130:{n['url'].split(':')[-1]}")

client.disconnect()
print("\n完成!")
