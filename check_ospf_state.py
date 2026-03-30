# -*- coding: utf-8 -*-
"""OSPF实验状态诊断"""
import sys
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

from scripts.client import EVEClient
import json

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
print("Connected!")

lab_path = "/OSPF_Routing_Lab.unl"

# 1. 节点状态
print("\n=== 节点状态 ===")
nodes = client.client.api.list_nodes(lab_path)
print(json.dumps(nodes, indent=2, ensure_ascii=False))

# 2. 网络列表
print("\n=== 网络列表 ===")
nets = client.client.api.list_lab_networks(lab_path)
print(json.dumps(nets, indent=2, ensure_ascii=False))

# 3. 拓扑信息
print("\n=== 拓扑 ===")
topo = client.client.api.get_lab_topology(lab_path)
print(json.dumps(topo, indent=2, ensure_ascii=False))

# 4. 尝试手动连接测试（查API接口）
print("\n=== 链路连接测试 ===")
# 先找 node_id 和 net_id
node_info_r1 = client.client.api.get_node_by_name(lab_path, "R1")
print(f"R1 info: {json.dumps(node_info_r1, indent=2, ensure_ascii=False)}")
net_info_net1 = client.client.api.get_lab_network_by_name(lab_path, "Net1")
print(f"Net1 info: {json.dumps(net_info_net1, indent=2, ensure_ascii=False)}")

# 尝试用node_id连接
if node_info_r1 and net_info_net1:
    r1_id = node_info_r1.get('id')
    net1_id = net_info_net1.get('id')
    print(f"\n尝试连接 R1(id={r1_id}) eth0 -> Net1(id={net1_id})")
    # connect_node_to_cloud 需要 src(nodename), src_label(iface), dst(cloudname)
    # 试试直接用API
    try:
        resp = client.client.api.connect_node_to_cloud(lab_path, "R1", "eth0", "Net1")
        print(f"connect_node_to_cloud result: {json.dumps(resp, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"connect_node_to_cloud error: {e}")

client.disconnect()
print("\nDone!")
