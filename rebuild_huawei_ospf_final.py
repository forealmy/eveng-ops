# -*- coding: utf-8 -*-
"""华为OSPF - 清理所有实验后再重建"""
import sys, time
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
builder = LabBuilder(client)
controller = LabController(client)

# 先停掉所有可能存在的lab的节点
print("[1] 停止所有实验的节点")
for lab_name in ["Huawei_OSPF", "Huawei_Test", "OSPF_Huawei_Lab", "OSPF_H3C_Lab"]:
    lab_path = f"/{lab_name}.unl"
    if builder.lab_exists(lab_path):
        try:
            nodes = client.client.api.list_nodes(lab_path)
            for nid, n in nodes.get('data', {}).items():
                if n.get('status') != 0:
                    r = client.client.api.stop_node(lab_path, n['name'])
                    print(f"  stop {lab_name}/{n['name']}: {r.get('message', r)}")
        except Exception as e:
            print(f"  {lab_name}: {e}")
print("等待10秒...")
time.sleep(10)

# 删除所有旧lab
print("\n[2] 删除所有实验")
for lab_name in ["Huawei_OSPF", "Huawei_Test", "OSPF_Huawei_Lab", "OSPF_H3C_Lab"]:
    if builder.lab_exists(f"/{lab_name}.unl"):
        builder.delete_lab(f"/{lab_name}.unl")
        print(f"  删除 {lab_name}")
time.sleep(2)

# 创建新lab
print("\n[3] 创建 Huawei_OSPF")
builder.create_lab(lab_name="Huawei_OSPF", lab_path="/", author="admin",
    description="华为AR1K OSPF路由实验")
time.sleep(1)

# 创建网络
print("[4] 创建网络")
for net in ["Net1", "Net2", "Net3"]:
    r = client.client.api.add_lab_network("/Huawei_OSPF.unl", "bridge", 1, name=net)
    print(f"  {net}: {r.get('status')}")
time.sleep(2)

# 创建节点
print("[5] 创建3个华为AR1K节点")
for node in ["R1", "R2", "R3"]:
    r = client.client.api.add_node("/Huawei_OSPF.unl", "huaweiar1k", 0,
        name=node, node_type="qemu", console="telnet", ram=2048, ethernet=8)
    print(f"  {node}: {r.get('status')}")
    time.sleep(1)

# 验证接口
print("\n[6] 验证接口")
for node in ["R1", "R2", "R3"]:
    ni = builder.get_node_by_name("/Huawei_OSPF.unl", node)
    ifs = client.client.api.get_node_interfaces("/Huawei_OSPF.unl", ni['id'])
    eths = [e['name'] for e in ifs.get('data',{}).get('ethernet',[])]
    print(f"  {node}: {eths}")

# 启动节点（先不连链路）
print("\n[7] 启动节点")
start = controller.start_all_nodes("/Huawei_OSPF.unl")
for r in start:
    print(f"  {r['name']}: {r['result'].get('message')}")

print("\n[8] 等待30秒让系统完全启动...")
time.sleep(30)

# 检查telnet响应
import socket
print("\n[9] 检查console响应")
nodes = client.client.api.list_nodes("/Huawei_OSPF.unl")
status_map = {0:'stopped', 1:'starting', 2:'stopping', 3:'running', 4:'paused', 99:'error'}
for nid, n in nodes.get('data', {}).items():
    port = int(n['url'].split(':')[-1])
    try:
        s = socket.socket()
        s.settimeout(10)
        s.connect(('192.168.73.130', port))
        s.send(b"\r\n")
        time.sleep(3)
        data = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
        except: pass
        s.close()
        text = data.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '')
        lines = [l for l in text.split('\n') if l.strip()]
        print(f"  {n['name']}: port={port} status={status_map.get(n.get('status'), n.get('status'))}")
        print(f"    telnet: {len(data)}字节, {len(lines)}行:")
        for l in lines[:8]:
            print(f"      {l[:100]}")
    except Exception as e:
        print(f"  {n['name']}: port={port} 连接失败: {e}")

# 连链路
print("\n[10] 连接链路")
links = [
    ("R1", "G0/0/0", "Net1"),
    ("R1", "G0/0/1", "Net2"),
    ("R2", "G0/0/0", "Net2"),
    ("R2", "G0/0/1", "Net3"),
    ("R3", "G0/0/0", "Net3"),
]
for node, iface, net in links:
    try:
        r = client.client.api.connect_node_to_cloud("/Huawei_OSPF.unl", node, iface, net)
        print(f"  {node}[{iface}]->{net}: {r.get('status')} {r.get('message','')[:60]}")
    except Exception as e:
        print(f"  {node}[{iface}]->{net}: ERROR {e}")
    time.sleep(0.5)

print("\n完成!")
client.disconnect()
