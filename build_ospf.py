import sys
import traceback
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')

try:
    from scripts.client import EVEClient
    from scripts.lab_builder import LabBuilder
    from scripts.lab_controller import LabController

    print("Connecting to EVE-NG...")
    client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
    client.connect()
    print("Connected!")

    builder = LabBuilder(client)

    # Delete existing lab if it exists
    lab_name = "OSPF_Routing_Lab"
    lab_path = f"/{lab_name}.unl"
    print(f"Checking if lab exists: {lab_path}")
    if builder.lab_exists(lab_path):
        print(f"Deleting existing lab...")
        builder.delete_lab(lab_path)
        print("Deleted.")
    else:
        # Try without leading slash
        if builder.lab_exists(f"{lab_name}.unl"):
            print(f"Deleting existing lab (no slash)...")
            builder.delete_lab(f"{lab_name}.unl")
            print("Deleted.")

    print("\nBuilding OSPF lab from YAML...")
    result = builder.build_from_yaml(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\templates\ospf_lab.yaml')
    print("Build result:")
    print(f"  Lab path: {result.get('lab_path')}")
    print(f"  Lab created: {result.get('lab_created')}")
    for n in result.get('networks', []):
        print(f"  Network {n['name']}: {n['result'].get('status')} - {n['result'].get('message', '')[:80]}")
    for n in result.get('nodes', []):
        print(f"  Node {n['name']}: {n['result'].get('status')} - {n['result'].get('message', '')[:80]}")
    for l in result.get('links', []):
        print(f"  Link {l['link']}: {l['result'].get('status')}")

    lab_path_out = result.get('lab_path', '')
    print(f"\nLab path for next steps: {repr(lab_path_out)}")

    # Start all nodes
    print("\nStarting all nodes...")
    controller = LabController(client)
    start_result = controller.start_all_nodes(lab_path_out)
    print("Start result:", start_result)

    # List node status
    print("\nListing node status...")
    import json
    nodes_data = builder.list_nodes(lab_path_out)
    print(json.dumps(nodes_data, indent=2, ensure_ascii=False))

except Exception as e:
    traceback.print_exc()
