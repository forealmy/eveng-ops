import sys
import json
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient
    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    
    print("Listing node templates...")
    result = client.client.api.list_node_templates()
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    import traceback
    traceback.print_exc()
