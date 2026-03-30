# -*- coding: utf-8 -*-
"""通过EVE-NG API获取节点详细信息和console状态"""
import sys
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
import json

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()

print("=== API获取节点详细信息 ===")
for lab_name in ["OSPF_Huawei_Lab", "OSPF_H3C_Lab"]:
    lab_path = f"/{lab_name}.unl"
    print(f"\n--- {lab_name} ---")
    try:
        nodes = client.client.api.list_nodes(lab_path)
        for nid, ndata in nodes.get('data', {}).items():
            print(f"\n  节点: {ndata['name']}")
            print(f"    完整数据: {json.dumps({k: v for k, v in ndata.items() if k != 'none'}, indent=4, ensure_ascii=False)}")

            # 获取节点接口详情
            ifaces = client.client.api.get_node_interfaces(lab_path, nid)
            print(f"    接口详情:")
            for iface_type, iface_list in ifaces.get('data', {}).items():
                for iface in iface_list:
                    print(f"      {iface_type}: {json.dumps(iface)}")
    except Exception as e:
        print(f"  错误: {e}")

# 尝试获取lab的原始JSON数据
print("\n\n=== Lab原始数据 ===")
for lab_name in ["OSPF_Huawei_Lab"]:
    lab_path = f"/{lab_name}.unl"
    try:
        lab_info = client.client.api.get_lab(lab_path)
        print(f"\n{lab_name}:")
        print(json.dumps(lab_info.get('data', {}).get('lab', {}), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"  错误: {e}")

client.disconnect()
