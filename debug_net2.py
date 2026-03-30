import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    api = client.client.api

    lab_path = '/OSPF_Routing_Lab.unl'

    # Get lab info
    print("Getting lab info...")
    info = api.get_lab(lab_path)
    print(json.dumps(info, indent=2, ensure_ascii=False)[:1000])

    # Get lab topology
    print("\nGetting lab topology...")
    topo = api.get_lab_topology(lab_path)
    print(json.dumps(topo, indent=2, ensure_ascii=False)[:3000])

    # List networks - look at raw URL being called
    print("\nChecking raw response for list_networks...")
    import requests
    base_url = 'http://192.168.73.130'
    # Get the session cookies
    resp = api.get_lab(lab_path)  # This sets up session
    print(f"Session established, cookies: {dict(api.session.cookies)}")

    # Manually call the API with the correct path
    path_normalized = '/OSPF_Routing_Lab.unl'
    url = f"{base_url}/api/labs{path_normalized}/networks"
    print(f"Fetching: {url}")
    r = api.session.get(url, verify=False)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:1000]}")

except Exception as e:
    import traceback
    traceback.print_exc()
