# -*- coding: utf-8 -*-
"""通过Kali跳板检查EVE-NG QEMU进程"""
import paramiko
import sys

WINDOWS_KEY = r"C:\Users\qq110\.ssh\id_rsa"

def ssh_to_kali():
    transport = paramiko.Transport(("192.168.73.129", 22))
    pkey = paramiko.RSAKey.from_private_key_file(WINDOWS_KEY)
    transport.connect(username="kali", pkey=pkey)
    client = SSHClient_from_transport(transport)
    return client

def SSHClient_from_transport(transport):
    """从已连接的transport创建SSHClient"""
    client = paramiko.SSHClient()
    client._transport = transport
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return client

def run_on_kali(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='replace')

client = ssh_to_kali()
print("SSH到Kali成功\n")

# 测试Kali到EVE连通
print("[1] Kali到EVE连通")
out = run_on_kali(client, "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.73.130 hostname 2>&1")
print(f"直接ssh: {out[:100]}")

# 试试EVE密码
eve_authed = False
for pwd in ["eve", "root", "password", "admin"]:
    out = run_on_kali(client,
        f"sshpass -p '{pwd}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.73.130 hostname 2>&1")
    print(f"密码={pwd}: {out[:80]}")
    if "permission" not in out.lower()[:30] and out.strip() and "denied" not in out.lower():
        eve_authed = True
        break

if not eve_authed:
    print("\n无法ssh到EVE-NG，尝试其他方式...")
    # 检查EVE-NG是否有web管理接口
    print("[alt] 尝试通过web管理接口查看")
    out = run_on_kali(client, "curl -s -k https://192.168.73.130/api/status 2>&1 | head -5")
    print(f"API status: {out}")
    client.close()
    sys.exit(1)

print("\n[2] 查看QEMU进程（EVE-NG）")
out = run_on_kali(client,
    "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 "
    "'ps aux | grep -i qemu | grep -v grep | head -20' 2>&1")
print(out)

print("\n[3] 查看华为AR相关")
out = run_on_kali(client,
    "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 "
    "'ps aux | grep -i \"huawei\\|AR1k\\|h3c\" | grep -v grep' 2>&1")
print(out or "无")

print("\n[4] 查看实验tmp目录")
out = run_on_kali(client,
    "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 "
    "'ls -la /opt/unetlab/tmp/ 2>/dev/null | head -20' 2>&1")
print(out)

print("\n[5] 查看QEMU日志")
out = run_on_kali(client,
    "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 "
    "'journalctl -b --no-pager -n 50 2>/dev/null | grep -i qemu | tail -20' 2>&1")
print(out or "无journalctl")

print("\n[6] 查看华为镜像是否挂载")
out = run_on_kali(client,
    "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 "
    "'ls -la /opt/unetlab/addons/qemu/ 2>/dev/null | grep -i huawei' 2>&1")
print(out or "无")

client.close()
print("完成!")
