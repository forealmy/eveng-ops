# -*- coding: utf-8 -*-
import sys, time
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
import socket

def test_port(host, port, send_cmd=b"\r\n"):
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((host, port))
        s.send(b"\r\n")  # 初始唤醒
        time.sleep(1)
        s.send(send_cmd)
        time.sleep(3)
        data = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        return data
    except Exception as e:
        return f"FAIL: {e}".encode()

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()

# 检查两个lab的节点状态
for lab_name in ["OSPF_Huawei_Lab", "OSPF_H3C_Lab"]:
    lab_path = f"/{lab_name}.unl"
    try:
        nodes = client.client.api.list_nodes(lab_path)
        if not nodes.get('data'):
            print(f"\n{lab_name}: 无数据（可能不存在）")
            continue
        print(f"\n=== {lab_name} ===")
        for nid, n in nodes.get('data', {}).items():
            url = n.get('url','')
            port = int(url.split(':')[-1])
            data = test_port('192.168.73.130', port)
            text = data.decode('utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '')
            lines = [l for l in text.split('\n') if l.strip()]
            status = 'stopped' if n.get('status') == 0 else f'status={n.get("status")}'
            print(f"  {n['name']}: port={port} {status}")
            print(f"    telnet响应 {len(data)} 字节, {len(lines)} 行:")
            for l in lines[:8]:
                print(f"      {l[:100]}")
    except Exception as e:
        print(f"\n{lab_name}: 错误 {e}")

client.disconnect()
