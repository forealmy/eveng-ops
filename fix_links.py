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

    # Try with Huawei-style interface names (GE0/0/0, GE0/0/1, etc.)
    links = [
        ['R1', 'GE0/0/0', 'Net1'],
        ['R1', 'GE0/0/1', 'Net2'],
        ['R2', 'GE0/0/0', 'Net2'],
        ['R2', 'GE0/0/1', 'Net3'],
        ['R3', 'GE0/0/0', 'Net3'],
    ]

    print("Attempting links with GE0/0/X interface names...")
    for link in links:
        try:
            resp = builder.connect(lab_path, link[0], link[1], link[2])
            print(f"  {link}: {resp.get('status')} - {resp.get('message', '')[:80]}")
        except Exception as e:
            print(f"  {link}: error - {e}")

    # Also try with Ethernet0/0 format
    links2 = [
        ['R1', 'Ethernet0/0/0', 'Net1'],
        ['R1', 'Ethernet0/0/1', 'Net2'],
        ['R2', 'Ethernet0/0/0', 'Net2'],
        ['R2', 'Ethernet0/0/1', 'Net3'],
        ['R3', 'Ethernet0/0/0', 'Net3'],
    ]
    print("\nAttempting links with Ethernet0/0/X interface names...")
    for link in links2:
        try:
            resp = builder.connect(lab_path, link[0], link[1], link[2])
            print(f"  {link}: {resp.get('status')} - {resp.get('message', '')[:80]}")
        except Exception as e:
            print(f"  {link}: error - {e}")

    # Also try simplified names
    links3 = [
        ['R1', 'eth0', 'Net1'],
        ['R1', 'eth1', 'Net2'],
        ['R2', 'eth0', 'Net2'],
        ['R2', 'eth1', 'Net3'],
        ['R3', 'eth0', 'Net3'],
    ]
    print("\nAttempting links with eth0/eth1 interface names...")
    for link in links3:
        try:
            resp = builder.connect(lab_path, link[0], link[1], link[2])
            print(f"  {link}: {resp.get('status')} - {resp.get('message', '')[:80]}")
        except Exception as e:
            print(f"  {link}: error - {e}")

except Exception as e:
    import traceback
    traceback.print_exc()
