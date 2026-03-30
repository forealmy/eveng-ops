import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient
    from scripts.lab_builder import LabBuilder

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    builder = LabBuilder(client)
    eveng_client = client.client
    session = eveng_client.session
    base_url = 'http://192.168.73.130'

    lab_path = '/OSPF_Routing_Lab.unl'

    # Connect using PUT to /labs/{path}/nodes/{node_id}/interfaces
    # Body: {"interface_index": "network_id"}
    # For R1: interface G0/0/0 = index 0, Net1 = id 1
    # For R1: interface G0/0/1 = index 1, Net2 = id 2
    # For R2: interface G0/0/0 = index 0, Net2 = id 2
    # For R2: interface G0/0/1 = index 1, Net3 = id 3
    # For R3: interface G0/0/0 = index 0, Net3 = id 3

    connections = [
        (1, 0, 1),  # R1, G0/0/0 (index 0), Net1 (id 1)
        (1, 1, 2),  # R1, G0/0/1 (index 1), Net2 (id 2)
        (2, 0, 2),  # R2, G0/0/0 (index 0), Net2 (id 2)
        (2, 1, 3),  # R2, G0/0/1 (index 1), Net3 (id 3)
        (3, 0, 3),  # R3, G0/0/0 (index 0), Net3 (id 3)
    ]

    print("Connecting routers to networks via PUT interface assignment...")
    for node_id, iface_idx, net_id in connections:
        url = f"{base_url}/api/labs{lab_path}/nodes/{node_id}/interfaces"
        data = json.dumps({str(iface_idx): str(net_id)})
        print(f"  PUT {url}")
        print(f"  Body: {data}")
        r = session.put(url, data=data, verify=False)
        resp = r.json()
        status = resp.get('status', 'unknown')
        msg = resp.get('message', str(resp)[:100])
        print(f"  Result: {status} - {msg}")
        print()

    # Check network counts
    print("Verifying network connections...")
    nets = builder.list_networks(lab_path)
    if nets.get('data'):
        for net_id_key, net_data in nets['data'].items():
            print(f"  {net_data.get('name')}: count={net_data.get('count')}")

    # Get node status
    print("\nVerifying node status...")
    nodes = builder.list_nodes(lab_path)
    if nodes.get('data'):
        for node_id, node_data in nodes['data'].items():
            print(f"  {node_data.get('name')}: status={node_data.get('status')} (2=running)")

except Exception as e:
    import traceback
    traceback.print_exc()
