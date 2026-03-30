# -*- coding: utf-8 -*-
"""通过Kali跳板检查EVE-NG的QEMU进程状态"""
import paramiko
import time

KALI_HOST = "192.168.73.129"
KALI_USER = "kali"
KALI_PASSWORD = "kali"

EVE_HOST = "192.168.73.130"
EVE_USER = "root"
# 试试常见密码
EVE_PASSWORDS = ["eve", "root", "password", "admin"]

def ssh_via_kali(cmd):
    """通过Kali跳板执行命令"""
    transport = paramiko.Transport((KALI_HOST, 22))
    transport.connect(username=KALI_USER, password=KALI_PASSWORD)
    kali_client = paramiko.SSHClient()
    kali_client.set_transport(transport)
    kali_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 通过Kali连接到EVE-NG
    # 使用kali作为跳板
    command = f"ssh -o StrictHostKeyChecking=no {EVE_USER}@{EVE_HOST} '{cmd}' 2>&1"
    stdin, stdout, stderr = kali_client.exec_command(command)
    output = stdout.read().decode()
    transport.close()
    return output

def try_eve_passwords(cmd):
    """尝试不同的EVE密码"""
    for pwd in EVE_PASSWORDS:
        try:
            transport = paramiko.Transport((KALI_HOST, 22))
            transport.connect(username=KALI_USER, password=KALI_PASSWORD)
            kali_client = paramiko.SSHClient()
            kali_client.set_transport(transport)
            kali_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            command = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE_USER}@{EVE_HOST} '{cmd}' 2>&1"
            stdin, stdout, stderr = kali_client.exec_command(command)
            output = stdout.read().decode()
            transport.close()
            print(f"  [{EVE_USER}@{EVE_HOST} 密码={pwd}]: {output[:200]}")
            if "password" not in output.lower() and "Permission" not in output:
                return output, pwd
        except Exception as e:
            print(f"  密码 {pwd} 失败: {e}")
    return None, None

# 先看kali到eve是否通
print("[1] 测试Kali到EVE-NG连通性")
transport = paramiko.Transport((KALI_HOST, 22))
transport.connect(username=KALI_USER, password=KALI_PASSWORD)
kali_client = paramiko.SSHClient()
kali_client.set_transport(transport)
kali_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

stdin, stdout, stderr = kali_client.exec_command(f"ping -c 2 -W 1 {EVE_HOST}")
ping_out = stdout.read().decode()
print(f"PING结果:\n{ping_out}")

# 试试ssh到eve-ng
print("\n[2] 测试SSH到EVE-NG（通过Kali跳板）")
for pwd in EVE_PASSWORDS:
    try:
        cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE_USER}@{EVE_HOST} 'hostname; uptime' 2>&1"
        stdin, stdout, stderr = kali_client.exec_command(cmd)
        output = stdout.read().decode()
        err = stderr.read().decode()
        print(f"  密码={pwd}: {output[:100]}")
        if output.strip() and "password" not in output.lower()[:20]:
            print(f"  ✅ 成功! 输出: {output[:100]}")
            break
    except Exception as e:
        print(f"  密码={pwd}: 失败 {e}")

transport.close()

# 如果SSH成功，看QEMU进程
print("\n[3] 查看QEMU进程（通过Kali跳板ssh到EVE）")
transport = paramiko.Transport((KALI_HOST, 22))
transport.connect(username=KALI_USER, password=KALI_PASSWORD)
kali_client = paramiko.SSHClient()
kali_client.set_transport(transport)
kali_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 多跳ssh
cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE_USER}@{EVE_HOST} 'ps aux | grep -i qemu | grep -v grep | head -20' 2>&1"
stdin, stdout, stderr = kali_client.exec_command(cmd)
output = stdout.read().decode()
print(f"QEMU进程:\n{output}")

# 看华为AR相关
cmd2 = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE_USER}@{EVE_HOST} 'ps aux | grep -i AR1000 | grep -v grep' 2>&1"
stdin, stdout, stderr = kali_client.exec_command(cmd2)
output2 = stdout.read().decode()
print(f"华为AR1000进程:\n{output2 or '无'}")

# 看console日志
cmd3 = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE_USER}@{EVE_HOST} 'ls /opt/unetlab/tmp/ 2>/dev/null | head -20' 2>&1"
stdin, stdout, stderr = kali_client.exec_command(cmd3)
output3 = stdout.read().decode()
print(f"实验tmp目录:\n{output3}")

transport.close()
print("\n完成!")
