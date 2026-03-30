# -*- coding: utf-8 -*-
"""OSPF实验 - H3C vSR1000，用Gi接口名"""
import sys
import time
import socket
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

def telnet_test(host, port, timeout=5):
    """测试节点是否真实运行"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(b"\r\n")
        time.sleep(1)
        data = s.recv(1024)
        s.close()
        return data.decode('ascii', errors='ignore').strip()[:100]
    except:
        return "connection failed"

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()

builder = LabBuilder(client)
controller = LabController(client)
lab_path = "/OSPF_H3C_Lab.unl"

# 检查节点真实状态
print("=== 检查节点真实运行状态 ===")
nodes = client.client.api.list_nodes(lab_path)
status_map = {0:'stopped',1:'starting',2:'stopping',3:'running',4:'paused',99:'error'}
for nid, ndata in nodes.get('data', {}).items():
    url = ndata.get('url','')
    port = int(url.split(':')[-1])
    host = url.split('://')[1].split(':')[0]
    telnet_result = telnet_test(host, port)
    api_status = status_map.get(ndata.get('status'), ndata.get('status'))
    print(f"  {ndata['name']}: API={api_status} telnet={telnet_result[:50]}")

# 节点启动后连接链路（Gi接口格式）
print("\n=== 连接链路（H3C Gi接口） ===")
links = [
    ("R1", "Gi1/0", "Net1"),
    ("R1", "Gi2/0", "Net2"),
    ("R2", "Gi1/0", "Net2"),
    ("R2", "Gi2/0", "Net3"),
    ("R3", "Gi1/0", "Net3"),
]
for node, iface, net in links:
    try:
        r = client.client.api.connect_node_to_cloud(lab_path, node, iface, net)
        status = r.get('status')
        msg = r.get('message', '')[:80]
        print(f"  {node}[{iface}] -> {net}: {status} {msg}")
    except Exception as e:
        print(f"  {node}[{iface}] -> {net}: ERROR {e}")
    time.sleep(1)

# 最终验证
print("\n=== 最终状态 ===")
nodes = client.client.api.list_nodes(lab_path)
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
