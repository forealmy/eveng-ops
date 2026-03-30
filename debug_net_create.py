# -*- coding: utf-8 -*-
"""诊断网络创建问题"""
import sys
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

from scripts.client import EVEClient
import json

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
print("Connected!")

lab_path = "/OSPF_Routing_Lab.unl"

# 直接调用 add_lab_network 看看返回什么
print("\n=== 测试创建网络 NetA ===")
resp = client.client.api.add_lab_network(
    path=lab_path,
    name="NetA",
    network_type="bridge",
    visibility=1
)
print(f"add_lab_network raw response: {json.dumps(resp, indent=2, ensure_ascii=False)}")

# 列出所有网络
print("\n=== 列出网络 ===")
nets = client.client.api.list_lab_networks(lab_path)
print(json.dumps(nets, indent=2, ensure_ascii=False))

# 按名查找
print("\n=== 查找 NetA ===")
net = client.client.api.get_lab_network_by_name(lab_path, "NetA")
print(json.dumps(net, indent=2, ensure_ascii=False))

# 获取 lab 详细信息
print("\n=== Lab 信息 ===")
lab = client.client.api.get_lab(lab_path)
print(json.dumps(lab, indent=2, ensure_ascii=False))

client.disconnect()
