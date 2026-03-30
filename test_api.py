import sys
import traceback
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient

    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()

    # Try listing nodes with the existing lab path
    lab_path = '//OSPF_Routing_Lab.unl'
    print(f"Trying list_nodes with path: {repr(lab_path)}")

    # Normalize the path - strip leading double slashes
    lab_path_fixed = lab_path.lstrip('/')
    print(f"Fixed path: {repr(lab_path_fixed)}")

    # Try with the fixed path
    print("\nTrying list_nodes with fixed path...")
    try:
        result = client.client.api.list_nodes(lab_path_fixed)
        print("Result:", json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    # Also try the absolute path without the leading /
    print("\nTrying list_nodes with no leading slash...")
    try:
        result = client.client.api.list_nodes('OSPF_Routing_Lab.unl')
        print("Result:", json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    # Try with just the lab name
    print("\nTrying get_lab_info with just the name...")
    try:
        result = client.client.api.get_lab_info('OSPF_Routing_Lab.unl')
        print("Result:", json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

except Exception as e:
    traceback.print_exc()
