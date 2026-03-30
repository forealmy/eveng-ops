import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    eveng_client = client.client
    session = eveng_client.session
    base_url = 'http://192.168.73.130'

    # Try different interface names
    test_ifaces = ['eth0', 'eth1', 'eth2', 'Ethernet0', 'Ethernet1', 'Ethernet0/0', 'Ethernet0/1',
                   'GE0/0/0', 'GE0/0/1', 'GE0/0', 'GE0/0/0', 'GigabitEthernet0/0/0']

    lab_path = '/OSPF_Routing_Lab.unl'

    # First get the node info from the raw API
    url = f"{base_url}/api/labs{lab_path}/nodes/1"
    r = session.get(url, verify=False)
    print(f"GET /labs{lab_path}/nodes/1")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:2000]}")

except Exception as e:
    import traceback
    traceback.print_exc()
