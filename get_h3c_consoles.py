# -*- coding: utf-8 -*-
import sys, socket, time
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
nodes = client.client.api.list_nodes('/OSPF_H3C_Lab.unl')
for nid, n in nodes.get('data', {}).items():
    url = n['url']
    port = int(url.split(':')[-1])
    host = url.split('://')[1].split(':')[0]
    print(f"{n['name']}: telnet://{host}:{port} status={n['status']}")

# telnet测试R1
print("\n--- R1 telnet测试 ---")
s = socket.socket()
s.settimeout(5)
s.connect(('192.168.73.130', 32769))
s.send(b"\r\n")
time.sleep(1)
data = s.recv(4096)
print(data.decode('ascii', errors='replace'))
s.close()

client.disconnect()
