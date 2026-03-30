# -*- coding: utf-8 -*-
"""华为AR1K OSPF实验 - 先验证节点能启动"""
import sys
import time
import socket
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

def telnet_test(host, port, timeout=5):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(b"\r\n")
        time.sleep(1)
        data = s.recv(1024)
        s.close()
        return data.decode('ascii', errors='ignore').strip()[:80]
    except Exception as e:
        return f"failed: {e}"

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
print("Connected!")

builder = LabBuilder(client)
controller = LabController(client)

lab_name = "OSPF_Huawei_Lab"
lab_path = f"/{lab_name}.unl"

# 1. 删除旧lab
if builder.lab_exists(lab_path):
    print(f"[1] 删除旧 lab: {lab_path}")
    builder.delete_lab(lab_path)
    time.sleep(3)

# 2. 创建lab
print(f"[2] 创建 lab")
builder.create_lab(lab_name=lab_name, lab_path="/", author="admin", description="华为AR1K OSPF实验-启动验证")
time.sleep(1)

# 3. 创建3个华为AR1K节点，用正确参数（不传config）
# RAM=2048, ethernet=8, cpu不传(默认), config不传(Unconfigured), delay=0
print("[3] 创建华为AR1K节点（正确参数）")
print("    RAM=2048, ethernet=8, cpu=默认, config=默认")
for node_name in ["R1", "R2", "R3"]:
    r = client.client.api.add_node(
        lab_path,
        "huaweiar1k",   # template
        0,               # delay
        name=node_name,
        node_type="qemu",
        console="telnet",
        ram=2048,
        ethernet=8,
        # cpu 不传，用模板默认值
        # config 不传，用 "Unconfigured"
    )
    print(f"  {node_name}: {r.get('status')} {r.get('message','')[:60]}")
    time.sleep(1)

# 4. 验证节点参数
print("\n[4] 验证节点参数")
for node_name in ["R1", "R2", "R3"]:
    ni = builder.get_node_by_name(lab_path, node_name)
    if ni:
        print(f"  {node_name}: ram={ni.get('ram')}, ethernet={ni.get('ethernet')}, cpu={ni.get('cpu')}")

# 5. 启动所有节点（不连链路，纯验证启动）
print("\n[5] 启动所有节点")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message')}")

# 6. 等待节点 UP
print("\n[6] 等待节点启动（最多60秒）...")
status_map = {0:'stopped', 1:'starting', 2:'stopping', 3:'running', 4:'paused', 99:'error'}
for i in range(60):
    time.sleep(1)
    nodes = client.client.api.list_nodes(lab_path)
    running = []
    for nid, ndata in nodes.get('data', {}).items():
        url = ndata.get('url','')
        port = int(url.split(':')[-1])
        host = url.split('://')[1].split(':')[0]
        tn = telnet_test(host, port)
        api_status = status_map.get(ndata.get('status'), ndata.get('status'))
        running.append(api_status)
        if i % 10 == 0 or api_status == 'running':
            print(f"  {ndata['name']}: API={api_status} telnet={tn[:40]}")
    if all(s == 'running' for s in running):
        print(f"  {i+1}秒: 全部 UP!")
        break
    if i == 59:
        print("  60秒到，节点未全部 UP")

# 7. 最终状态
print("\n[7] 最终状态")
nodes = client.client.api.list_nodes(lab_path)
for nid, ndata in nodes.get('data', {}).items():
    url = ndata.get('url','')
    port = int(url.split(':')[-1])
    host = url.split('://')[1].split(':')[0]
    tn = telnet_test(host, port)
    s = status_map.get(ndata.get('status'), ndata.get('status'))
    ifaces = client.client.api.get_node_interfaces(lab_path, nid)
    eths = [e['name'] for e in ifaces.get('data',{}).get('ethernet',[])]
    print(f"  {ndata['name']}: {s} | telnet={tn[:50]}")
    print(f"    接口: {eths}")

client.disconnect()
print("\n完成!")
