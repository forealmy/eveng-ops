# -*- coding: utf-8 -*-
"""华为AR1K单节点启动测试"""
import sys, time, socket
sys.path.insert(0, r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops')
from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder
from scripts.lab_controller import LabController

client = EVEClient.from_config(r'C:\Users\qq110\.openclaw\workspace\skills\eveng-ops\config\eveng_config.json')
client.connect()
builder = LabBuilder(client)
controller = LabController(client)

lab_name = "Huawei_Test"
lab_path = f"/{lab_name}.unl"

# 删除旧lab（所有可能有冲突的）
print("[1] 清理旧lab")
for old_lab in ["Huawei_Test", "OSPF_Huawei_Lab", "OSPF_H3C_Lab"]:
    if builder.lab_exists(f"/{old_lab}.unl"):
        print(f"  删除 {old_lab}")
        builder.delete_lab(f"/{old_lab}.unl")
time.sleep(2)

# 创建lab
print("[2] 创建测试lab")
builder.create_lab(lab_name=lab_name, lab_path="/", author="admin", description="华为AR1K单节点启动测试")
time.sleep(1)

# 只创建1个节点
print("[3] 创建单节点 R1")
r = client.client.api.add_node(lab_path, "huaweiar1k", 0,
    name="R1", node_type="qemu", console="telnet",
    ram=2048, ethernet=8)
print(f"  结果: {r.get('status')} {r.get('message','')[:60]}")
time.sleep(2)

# 获取节点信息
ni = builder.get_node_by_name(lab_path, "R1")
print(f"  节点ID: {ni.get('id')}, url: {ni.get('url')}")
port = int(ni.get('url','').split(':')[-1])
print(f"  console端口: {port}")

# 启动节点
print("[4] 启动节点")
start_result = controller.start_all_nodes(lab_path)
for r in start_result:
    print(f"  {r['name']}: {r['result'].get('message')}")

# 等待15秒让boot开始
print("[5] 等待15秒...")
time.sleep(15)

# 读取console输出
print("[6] 读取console (9600速率)")
s = socket.socket()
s.settimeout(10)
s.connect(('192.168.73.130', port))
# 清空初始数据
time.sleep(2)
try:
    s.recv(8192)
except:
    pass

# 发回车触发输出
s.send(b"\r\n")
time.sleep(5)
data = b""
while True:
    try:
        chunk = s.recv(4096)
        if not chunk: break
        data += chunk
    except socket.timeout:
        break
s.close()

print(f"\n收到 {len(data)} 字节")
text = data.decode('utf-8', errors='replace')
lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
print(f"{len(lines)} 行:")
for i, l in enumerate(lines):
    if l.strip():
        print(f"  [{i}] {l[:120]}")
        if i > 40:
            print("  ...")
            break

# 写文件
with open(r'C:\Users\qq110\.openclaw\workspace\.cache\huawei_test_console.txt', 'w', encoding='utf-8', errors='replace') as f:
    f.write(text)
print(f"\n完整内容已保存到缓存文件")

# 检查节点状态
print("\n[7] 节点最终状态")
nodes = client.client.api.list_nodes(lab_path)
for nid, n in nodes.get('data', {}).items():
    print(f"  {n['name']}: status={n.get('status')} url={n.get('url')}")

client.disconnect()
print("\n完成!")
