"""
M2 测试脚本：拓扑快速构建测试
"""
import sys
sys.path.insert(0, 'C:/Users/qq110/.openclaw/workspace/skills/eveng-ops/scripts')

from client import EVEClient
from lab_builder import LabBuilder

# 连接
client = EVEClient.from_config()
client.connect()
print('Connected:', client.is_connected())

# 1. 列出现有实验室
labs = client.list_labs()
print('\n=== 现有实验室 ===')
for lab in labs[:10]:
    path = lab.get('path', lab.get('source_folder', ''))
    name = lab.get('name', '')
    print(f'  {path}/{name}')

# 2. 创建测试实验
builder = LabBuilder(client)
LAB_NAME = 'test_build_lab'
LAB_PATH = f'/{LAB_NAME}.unl'

print(f'\n=== 创建测试实验 {LAB_NAME} ===')
create_resp = builder.create_lab(lab_name=LAB_NAME, lab_path='/', author='admin', description='M2 test lab')
print('create_resp:', create_resp)

# 3. 列出可用模板（只看前5个key）
print('\n=== 可用节点模板 ===')
templates_resp = builder.list_templates()
tmpl_keys = list(templates_resp.get('data', {}).keys())
print('Templates:', tmpl_keys[:10])

# 4. 创建一个简单节点
print('\n=== 添加节点 TestNode1 ===')
node_resp = builder.create_node(
    lab_path=LAB_PATH,
    name='TestNode1',
    template='vpcs',
    node_type='vpcs',
)
print('node_resp:', node_resp)

# 5. 列出节点确认创建成功
print('\n=== 列出节点 ===')
nodes_resp = builder.list_nodes(LAB_PATH)
print('nodes_resp:', nodes_resp)
if nodes_resp.get('status') == 'success':
    nodes_data = nodes_resp.get('data', {})
    print(f'节点数量: {len(nodes_data)}')
    for nid, ninfo in nodes_data.items():
        print(f'  ID={nid} Name={ninfo.get("name")} Template={ninfo.get("template")}')

# 6. 删除测试实验（清理）
print('\n=== 删除测试实验 ===')
del_resp = builder.delete_lab(LAB_PATH)
print('delete_resp:', del_resp)

# 断开
client.disconnect()
print('\nDone. Disconnected.')
