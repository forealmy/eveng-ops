# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
nodes = client.client.api.list_nodes('/OSPF_Routing_Lab.unl')
for nid, n in nodes['data'].items():
    print(f"{n['name']}: telnet://{n['url'].split('://')[1]}  [status={n['status']}]")
client.disconnect()
