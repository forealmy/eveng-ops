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

    # Try connecting with 'eth0', 'eth1', 'eth2' interface names
    links = [
        ['R1', 'eth0', 'Net1'],
        ['R1', 'eth1', 'Net2'],
        ['R2', 'eth0', 'Net2'],
        ['R2', 'eth1', 'Net3'],
        ['R3', 'eth0', 'Net3'],
    ]

    print("Trying connections with ethX interface names...")
    for link in links:
        node, iface, net = link
        # Use the raw API call to connect
        url = f"{base_url}/api/labs{lab_path}/connect/node-to-cloud"
        data = {
            'node': node,
            'src_label': iface,
            'dst': net
        }
        r = session.post(url, json=data, verify=False)
        resp = r.json()
        status = resp.get('status', 'unknown')
        msg = resp.get('message', str(resp)[:100])
        print(f"  {node} {iface} -> {net}: {status} - {msg}")

    # Check network counts
    print("\nChecking network counts...")
    nets = builder.list_networks(lab_path)
    if nets.get('data'):
        for net_id, net_data in nets['data'].items():
            print(f"  {net_data.get('name')}: count={net_data.get('count')}")

except Exception as e:
    import traceback
    traceback.print_exc()
