import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient
    from scripts.lab_builder import LabBuilder

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    builder = LabBuilder(client)

    lab_path = '/OSPF_Routing_Lab.unl'

    # Huawei AR interface names
    links = [
        ['R1', 'GE0/0/0', 'Net1'],
        ['R1', 'GE0/0/1', 'Net2'],
        ['R2', 'GE0/0/0', 'Net2'],
        ['R2', 'GE0/0/1', 'Net3'],
        ['R3', 'GE0/0/0', 'Net3'],
    ]

    print("Connecting routers to networks...")
    for link in links:
        node, iface, net = link
        try:
            resp = builder.connect(lab_path, node, iface, net)
            status = resp.get('status', 'unknown')
            msg = resp.get('message', str(resp)[:80])
            print(f"  {node} {iface} -> {net}: {status} - {msg}")
        except Exception as e:
            print(f"  {node} {iface} -> {net}: ERROR - {e}")

    # Also verify node list
    print("\nVerifying node list...")
    nodes = builder.list_nodes(lab_path)
    if nodes.get('data'):
        for node_id, node_data in nodes['data'].items():
            print(f"  Node {node_id}: {node_data.get('name')} - ethernet={node_data.get('ethernet')}")

    # Verify network list (check counts)
    print("\nVerifying networks...")
    nets = builder.list_networks(lab_path)
    if nets.get('data'):
        for net_id, net_data in nets['data'].items():
            print(f"  Network {net_id}: {net_data.get('name')} - count={net_data.get('count')}")

except Exception as e:
    import traceback
    traceback.print_exc()
