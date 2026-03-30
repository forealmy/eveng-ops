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

    # List networks
    print("Listing networks in lab...")
    networks = builder.list_networks(lab_path)
    print(json.dumps(networks, indent=2, ensure_ascii=False))

    # Get lab topology
    print("\nGetting lab topology...")
    topo = builder.get_lab_topology(lab_path)
    print(json.dumps(topo, indent=2, ensure_ascii=False)[:2000])

    # Also try without leading slash
    print("\nListing networks without leading slash...")
    networks2 = builder.list_networks('OSPF_Routing_Lab.unl')
    print(json.dumps(networks2, indent=2, ensure_ascii=False))

except Exception as e:
    import traceback
    traceback.print_exc()
