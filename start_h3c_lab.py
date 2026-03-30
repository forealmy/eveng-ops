# -*- coding: utf-8 -*-
import sys, time, socket
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
controller = LabController(client)
lab_path = "/OSPF_H3C_Lab.unl"

print("=== 启动H3C OSPF实验 ===")
print("当前链路状态:")
nets = client.client.api.list_lab_networks(lab_path)
for nid, n in nets.get('data', {}).items():
    print(f"  {n['name']}: count={n['count']}")

print("\n启动所有节点...")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message')}")

print("\n等待10秒让节点启动...")
time.sleep(10)

print("\n检查telnet连通性:")
nodes = client.client.api.list_nodes(lab_path)
status_map = {0:'stopped',1:'starting',2:'stopping',3:'running',4:'paused',99:'error'}
for nid, n in nodes.get('data', {}).items():
    url = n['url']
    port = int(url.split(':')[-1])
    host = url.split('://')[1].split(':')[0]
    # 测试telnet
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((host, port))
        s.send(b"\r\n")
        time.sleep(1)
        data = s.recv(4096)
        s.close()
        tn_result = data.decode('ascii', errors='ignore').replace('\r\n', ' ').replace('\r', ' ').strip()[:60]
    except Exception as e:
        tn_result = f"FAIL: {e}"
    print(f"  {n['name']}: API={status_map.get(n['status'], n['status'])} telnet={tn_result}")

client.disconnect()
print("\n完成!")
