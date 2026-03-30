# -*- coding: utf-8 -*-
"""华为OSPF实验 - 重启节点并立即检查console"""
import sys, time, socket
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
from scripts.lab_controller import LabController
import json

def telnet_raw_read(host, port, cmds, timeout=3):
    """发送命令并读取响应"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(b"\r\n")
        time.sleep(0.5)
        # 读取初始输出
        data = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                break
        text = data.decode('ascii', errors='ignore')
        
        # 发送命令
        for cmd in cmds:
            s.send(f"{cmd}\r\n".encode())
            time.sleep(1)
            data = b""
            while True:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
            text += data.decode('ascii', errors='ignore')
        
        s.close()
        return text
    except Exception as e:
        return f"Error: {e}"

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
controller = LabController(client)
lab_path = "/OSPF_Huawei_Lab.unl"

print("=== 当前节点状态 ===")
nodes = client.client.api.list_nodes(lab_path)
status_map = {0:'stopped',1:'starting',2:'stopping',3:'running',4:'paused',99:'error'}
for nid, ndata in nodes.get('data', {}).items():
    print(f"  {ndata['name']}: status={status_map.get(ndata['status'], ndata['status'])} url={ndata['url']}")
    print(f"    image={ndata.get('image')} ram={ndata.get('ram')} eth={ndata.get('ethernet')}")

print("\n=== 停止所有节点 ===")
for nid, ndata in nodes.get('data', {}).items():
    if ndata['status'] != 0:  # not already stopped
        r = client.client.api.stop_node(lab_path, ndata['name'])
        print(f"  stop {ndata['name']}: {r}")
        time.sleep(2)

print("\n等待5秒...")
time.sleep(5)

print("\n=== 启动所有节点 ===")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  start {r['name']}: {r['result'].get('message')}")

print("\n=== 立即telnet检查（启动后5秒内）===")
time.sleep(5)
nodes = client.client.api.list_nodes(lab_path)
for nid, ndata in nodes.get('data', {}).items():
    url = ndata['url']
    port = int(url.split(':')[-1])
    host = url.split('://')[1].split(':')[0]
    print(f"\n  {ndata['name']} telnet到 {host}:{port}:")
    
    # 读取初始输出
    text = telnet_raw_read(host, port, [], timeout=3)
    lines = [l for l in text.split('\r\n') if l.strip()]
    print("    前10行输出:")
    for l in lines[:10]:
        print(f"      {l}")
    
    # 尝试按回车看提示符
    text2 = telnet_raw_read(host, port, [""], timeout=3)
    lines2 = [l for l in text2.split('\r\n') if l.strip()]
    print("    按回车后:")
    for l in lines2[:10]:
        print(f"      {l}")

print("\n=== 30秒后再检查 ===")
time.sleep(30)
nodes = client.client.api.list_nodes(lab_path)
for nid, ndata in nodes.get('data', {}).items():
    s = status_map.get(ndata['status'], ndata['status'])
    print(f"  {ndata['name']}: status={s}")

client.disconnect()
print("\n完成!")
