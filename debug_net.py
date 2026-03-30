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
    lab_path2 = 'OSPF_Routing_Lab.unl'

    # Create networks directly
    print("Creating Net1...")
    r1 = client.client.api.add_lab_network(path=lab_path, name='Net1', network_type='bridge', visibility=0)
    print(json.dumps(r1, indent=2))

    print("\nCreating Net2...")
    r2 = client.client.api.add_lab_network(path=lab_path, name='Net2', network_type='bridge', visibility=0)
    print(json.dumps(r2, indent=2))

    print("\nCreating Net3...")
    r3 = client.client.api.add_lab_network(path=lab_path, name='Net3', network_type='bridge', visibility=0)
    print(json.dumps(r3, indent=2))

    print("\nListing networks (with slash)...")
    print(json.dumps(builder.list_networks(lab_path), indent=2))

    print("\nListing networks (without slash)...")
    print(json.dumps(builder.list_networks(lab_path2), indent=2))

    print("\nget_network_by_name Net1 (with slash)...")
    print(json.dumps(builder.get_network_by_name(lab_path, 'Net1'), indent=2))

    print("\nget_network_by_name Net1 (without slash)...")
    print(json.dumps(builder.get_network_by_name(lab_path2, 'Net1'), indent=2))

except Exception as e:
    import traceback
    traceback.print_exc()
