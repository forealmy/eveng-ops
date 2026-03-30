# EVE-NG Skill - 完整操作手册 (M1–M6)

> EVE-NG（Emulated Virtual Environment Next Generation）网络模拟平台操作技能模块。
> 支持连接管理、拓扑构建、启停控制、配置注入、Kali 联动、预置靶场模板。

---

## 目录结构

```
eveng-ops/
├── SKILL.md              ← 本文件
├── scripts/
│   ├── client.py            # M1: EVE-NG 连接客户端
│   ├── lab_builder.py       # M2: 拓扑构建器
│   ├── lab_controller.py    # M3: 实验启停控制器
│   ├── config_manager.py    # M4: 配置注入与快照管理
│   ├── kali联动.py          # M5: Kali-ops 联动
│   └── test_m*.py           # 各模块测试脚本
├── config/
│   ├── eveng_config.json    # 连接配置
│   └── templates/           # 预置 YAML 模板
│       ├── simple_router.yaml      # 简单路由实验（2台 IOL）
│       ├── cisco_asa_fw.yaml       # ASA 防火墙演练
│       ├── metasploitable.yaml     # Kali + 靶机
│       ├── pentest_lab.yaml        # 渗透测试靶场（M6 新增）
│       └── multi_vendor.yaml       # 多厂商路由演练（M6 新增）
└── reports/                  # 输出目录
```

## 安装依赖

```bash
pip install eve-ng pyyaml
```

---

## 快速开始（3 行代码启动实验）

```python
from scripts.client import EVEClient
from scripts.lab_builder import LabBuilder

# 连接并从 YAML 构建拓扑
client = EVEClient.from_config()
builder = LabBuilder(client)
result = builder.build_from_yaml("config/templates/simple_router.yaml", lab_name="my_first_lab")
```

---

## M1 模块：连接管理

### EVEClient 快速上手

```python
from scripts.client import EVEClient

# 方式1：从 config/eveng_config.json 加载（推荐）
client = EVEClient.from_config()

# 方式2：直接指定参数
client = EVEClient(
    host="http://192.168.73.130",
    username="admin",
    password="eve",
    ssl_verify=False
)

client.connect()           # 登录
print(client.get_status()) # 获取服务器状态
labs = client.list_labs() # 列出所有实验
client.disconnect()        # 登出
```

### 配置文件格式

`config/eveng_config.json`:

```json
{
  "host": "http://192.168.73.130",
  "username": "admin",
  "password": "eve",
  "ssl_verify": false,
  "timeout": 30
}
```

### EVEClient API

| 方法 | 说明 |
|------|------|
| `connect()` | 登录 EVE-NG 服务器 |
| `disconnect()` | 登出 |
| `is_connected()` | 检查连接状态 |
| `get_status()` | 获取服务器状态 |
| `list_folders()` | 列出所有文件夹 |
| `list_labs()` | 列出所有实验 |
| `get_lab(path)` | 获取实验详情 |

---

## M2 模块：拓扑快速构建

### LabBuilder API

```python
from scripts.lab_builder import LabBuilder

builder = LabBuilder(client)
```

#### 核心方法

| 方法 | 说明 |
|------|------|
| `create_lab(name, path, author, description)` | 创建实验 |
| `delete_lab(lab_path)` | 删除实验 |
| `lab_exists(lab_path)` | 检查实验是否存在 |
| `create_node(lab_path, ...)` | 创建节点 |
| `list_nodes(lab_path)` | 列出所有节点 |
| `create_network(lab_path, name, type)` | 创建网络 |
| `connect(lab_path, node, iface, target, ...)` | 连接节点/网络 |
| `build_from_dict(topo_def)` | 从 dict 构建拓扑 |
| `build_from_yaml(yaml_path, lab_name?)` | 从 YAML 文件构建 |
| `list_templates()` | 列出可用模板 |
| `list_network_types()` | 列出网络类型 |

### YAML 格式说明

```yaml
lab_name: "my_lab"        # 实验名称
author: "admin"           # 作者
description: "..."        # 描述
nodes:                    # 节点列表
  - name: "Router1"       # 节点名称
    template: "iol"       # 模板：qemu / docker / iol / vpcs / dynamips
    image: "..."           # 镜像名称（可选）
    ram: 2048              # 内存 MB（可选）
    cpu: 1                 # CPU 数量（可选）
    ethernet: 4            # 接口组数（可选，每组4个接口）
    serial: 0              # 串行接口组数（可选）
    console: "telnet"      # 控制台类型：telnet / vnc（可选）
    type: "iol"            # 节点类型（可选，默认 qemu）
    left: 10; top: 20      # 画布位置百分比（可选）
networks:                  # 网络列表
  - name: "WAN"           # 网络名称
    type: "bridge"         # 网络类型：bridge / pnet / ovs / nat / etc.
    visibility: 1           # 可视化：0=隐藏 1=显示（可选）
links:                     # 链路列表
  - [Router1, eth0, WAN]           # 节点连网络
  - [Router1, eth0, Router2, eth0] # 节点连节点
```

### 从 YAML 构建拓扑

```python
# 方式1：从文件路径
result = builder.build_from_yaml(
    "config/templates/simple_router.yaml",
    lab_name="my_router_lab"  # 可选：覆盖 YAML 中的 lab_name
)

# 方式2：从 dict 直接构建
topo = {
    "lab_name": "my_lab",
    "nodes": [{"name": "R1", "template": "iol", "ethernet": 2}],
    "networks": [{"name": "WAN", "type": "bridge"}],
    "links": [["R1", "eth0", "WAN"]]
}
result = builder.build_from_dict(topo)
```

---

## M3 模块：启停控制（实验环境控制器）

### LabController API

```python
from scripts.lab_controller import LabController

controller = LabController(client)
```

#### 节点控制

| 方法 | 说明 |
|------|------|
| `start_node(lab_path, name)` | 启动指定节点 |
| `stop_node(lab_path, name)` | 停止指定节点 |
| `wipe_node(lab_path, name)` | 清除节点配置（恢复初始） |
| `get_node_status(lab_path, name)` | 获取节点运行状态 |

#### 批量控制

| 方法 | 说明 |
|------|------|
| `start_all_nodes(lab_path)` | 启动所有节点 |
| `stop_all_nodes(lab_path)` | 停止所有节点 |
| `wipe_all_nodes(lab_path)` | 重置所有节点 |

#### 实验级控制

| 方法 | 说明 |
|------|------|
| `start_lab(lab_path)` | 一键启动整个实验 |
| `stop_lab(lab_path)` | 一键停止整个实验 |

#### 状态监控

| 方法 | 说明 |
|------|------|
| `get_lab_status(lab_path)` | 获取实验整体状态 |
| `list_node_status(lab_path)` | 列出所有节点状态 |

### 状态码说明

| 状态码 | 含义 |
|--------|------|
| 0 | stopped |
| 1 | starting |
| 2 | stopping |
| 3 | running |
| 4 | paused |
| 99 | error |

---

## M4 模块：配置注入与快照管理

### ConfigManager API

```python
from scripts.config_manager import ConfigManager

cm = ConfigManager(client)
```

#### 配置操作

| 方法 | 说明 |
|------|------|
| `get_config(lab_path, node_name)` | 获取节点当前配置 |
| `get_all_configs(lab_path)` | 获取所有节点配置 |
| `upload_config(lab_path, node_name, config)` | 上传配置到节点 |
| `enable_startup_config(lab_path, node_name)` | 启用节点启动配置 |
| `export_node_config(lab_path, node_name, output_path)` | 导出配置到文件 |
| `export_all_configs(lab_path, output_dir)` | 导出所有节点配置 |
| `list_node_configs_summary(lab_path)` | 列出配置摘要 |

#### 快照与模板

| 方法 | 说明 |
|------|------|
| `export_lab(lab_path, output_dir)` | 导出实验为 .unl 文件 |
| `import_lab(unl_file, folder)` | 导入 .unl 文件创建实验 |
| `clone_lab(source_lab, dest_name, folder)` | 克隆实验 |
| `save_as_template(lab_path, template_name)` | 保存为模板 |

### 示例：配置 Cisco 路由器

```python
config = """interface Ethernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
"""
cm.upload_config("/my_lab.unl", "Router1", config)
```

---

## M5 模块：Kali-ops 联动

### Kali联动 API

```python
from scripts.kali联动 import Kali联动

kali = Kali联动(client)
```

#### 拓扑分析

| 方法 | 说明 |
|------|------|
| `get_lab_topology(lab_path)` | 获取完整拓扑（节点+网络+链路） |
| `get_node_console_ips(lab_path)` | 获取所有节点 console IP 和端口 |
| `find_gateway_nodes(lab_path)` | 查找边界节点（连接外部网络的路由器） |

#### 导出与渗透分析

| 方法 | 说明 |
|------|------|
| `export_topology_for_kali(lab_path, output_json)` | 导出为 Kali-ops 可用 JSON |
| `build_pentest_topology(lab_path)` | 生成渗透测试视角拓扑 |

#### Kali-ops 联动流程

```
EVE-NG 实验拓扑
      ↓ get_lab_topology()
      ↓ export_topology_for_kali()
      ↓ build_pentest_topology()
渗透测试 JSON → 输入到 kali-ops → 扫描报告
```

### 典型工作流

```python
# 1. 获取拓扑并导出给 Kali-ops
topo = kali.get_lab_topology("/pentest_lab.unl")
console_ips = kali.get_node_console_ips("/pentest_lab.unl")
gateways = kali.find_gateway_nodes("/pentest_lab.unl")

# 2. 导出为 Kali-ops 可解析的 JSON
kali.export_topology_for_kali("/pentest_lab.unl", "reports/topo.json")

# 3. 渗透测试视角分析
pentest = kali.build_pentest_topology("/pentest_lab.unl")
print(pentest["recommendations"])  # 攻击建议
```

---

## M6 模块：预置靶场模板

### 模板列表

| 文件 | 说明 | 节点 |
|------|------|------|
| `simple_router.yaml` | 简单路由实验 | 2× IOL 路由器 |
| `cisco_asa_fw.yaml` | ASA 防火墙演练 | ASA + 内网服务器 |
| `metasploitable.yaml` | 基础渗透靶场 | Kali + BTMS 靶机 |
| `pentest_lab.yaml` | 完整渗透靶场 | Kali + 靶机 + 边界路由器 |
| `multi_vendor.yaml` | 多厂商路由 | Cisco IOL + Juniper vSRX + Huawei |

### pentest_lab.yaml — 渗透测试靶场

```
[Kali] ←→ [LAN] ←→ [Router-Border] ←→ [WAN (外部)]
                ↑
         [Metasploitable]
```
适用于：内网横移、漏洞利用、边界穿越练习。

### multi_vendor.yaml — 多厂商路由演练

```
  [ISP-Cisco] ←—— Backbone ——→ [Core-Juniper] ←→ LAN
                                    ↑
                            [Border-Huawei]
```
适用于：OSPF/BGP 多厂商配置、Trunk 链路调测。

### 使用模板创建实验

```python
# 方式1：直接使用模板文件路径
result = builder.build_from_yaml(
    "config/templates/pentest_lab.yaml"
)

# 方式2：加载后修改参数再构建
import yaml
with open("config/templates/pentest_lab.yaml") as f:
    topo = yaml.safe_load(f)
topo["lab_name"] = "my_pentest"
result = builder.build_from_dict(topo)
```

---

## 测试验证

```bash
# M2 测试：拓扑构建
python scripts/test_m2.py

# M3 测试：启停控制
python scripts/test_m3.py

# M4 测试：配置管理
python scripts/test_m4.py

# M5 测试：Kali-ops 联动
python scripts/test_m5.py
```

---

## 与 Kali-ops 的联动方式

1. **拓扑导出**：在 EVE-NG 中构建实验拓扑，使用 `Kali联动.export_topology_for_kali()` 导出为 JSON
2. **资产导入**：将 JSON 中的节点信息（IP、端口、角色）导入 kali-ops 的资产列表
3. **边界节点识别**：使用 `find_gateway_nodes()` 识别边界路由器，确定攻击入口
4. **扫描与利用**：Kali-ops 对内网节点进行漏洞扫描和渗透
5. **配置回注**：发现漏洞后，通过 `ConfigManager.upload_config()` 将利用结果回注到 EVE-NG 实验

---

## 错误排查

| 症状 | 解决方法 |
|------|----------|
| `Connection refused` | 确认 EVE-NG 服务地址和端口正确 |
| `ssl.SSLError` | 设置 `ssl_verify=False` 或导入证书 |
| 节点启动失败 | 检查镜像是否已导入、内存是否足够 |
| 链路连接失败 | 确认接口名称正确（eth0/1/2...） |
| YAML 解析错误 | 检查缩进，使用空格而非 Tab |
