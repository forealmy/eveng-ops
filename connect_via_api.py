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

    # List networks to confirm they exist
    print("Listing networks...")
    nets = builder.list_networks(lab_path)
    print(json.dumps(nets, indent=2))

except Exception as e:
    import traceback
    traceback.print_exc()
