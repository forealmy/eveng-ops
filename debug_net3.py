import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()

    # EvengClient has session directly
    eveng_client = client.client
    session = eveng_client.session
    base_url = 'http://192.168.73.130'

    # Check our specific lab networks - raw API
    url2 = f"{base_url}/api/labs/OSPF_Routing_Lab.unl/networks"
    r2 = session.get(url2, verify=False)
    print(f"GET /api/labs/OSPF_Routing_Lab.unl/networks")
    print(f"  Status: {r2.status_code}")
    print(f"  Response: {r2.text[:1000]}")

    # Also try with / prefix (URL encoded)
    url3 = f"{base_url}/api/labs/%2FOSPF_Routing_Lab.unl/networks"
    r3 = session.get(url3, verify=False)
    print(f"\nGET /api/labs/%2FOSPF_Routing_Lab.unl/networks")
    print(f"  Status: {r3.status_code}")
    print(f"  Response: {r3.text[:1000]}")

    # Try creating a network and immediately listing it
    url4 = f"{base_url}/api/labs/OSPF_Routing_Lab.unl/networks"
    data = {"name": "TestNet", "type": "bridge", "visibility": 0}
    r4 = session.post(url4, json=data, verify=False)
    print(f"\nPOST /api/labs/OSPF_Routing_Lab.unl/networks")
    print(f"  Status: {r4.status_code}")
    print(f"  Response: {r4.text[:500]}")

    # Now list again
    r5 = session.get(url2, verify=False)
    print(f"\nGET /api/labs/OSPF_Routing_Lab.unl/networks (after create)")
    print(f"  Status: {r5.status_code}")
    print(f"  Response: {r5.text[:1000]}")

    # Try listing all labs
    url_labs = f"{base_url}/api/labs"
    r_labs = session.get(url_labs, verify=False)
    print(f"\nGET /api/labs")
    print(f"  Status: {r_labs.status_code}")
    labs_data = r_labs.json()
    print(f"  Data keys: {list(labs_data.get('data', {}).keys()) if isinstance(labs_data.get('data'), dict) else type(labs_data.get('data'))}")
    labs_list = labs_data.get('data', {})
    if isinstance(labs_list, list):
        for lab in labs_list:
            print(f"  Lab: {lab}")
    elif isinstance(labs_list, dict):
        for k, v in labs_list.items():
            print(f"  Folder/path: {k}")

except Exception as e:
    import traceback
    traceback.print_exc()
