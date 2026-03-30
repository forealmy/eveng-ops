import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    eveng_client = client.client
    api = eveng_client.api
    session = eveng_client.session
    base_url = 'http://192.168.73.130'

    lab_path = '/OSPF_Routing_Lab.unl'

    # Get node interfaces for R1 (node_id=1)
    print("Getting node interfaces for R1...")
    try:
        result = api.get_node_interfaces(lab_path, 1)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"API method failed: {e}")

    # Also try via raw API
    url = f"{base_url}/api/labs{lab_path}/nodes/1/interfaces"
    r = session.get(url, verify=False)
    print(f"\nRaw API: GET {url}")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:2000]}")

except Exception as e:
    import traceback
    traceback.print_exc()
