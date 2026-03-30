# -*- coding: utf-8 -*-
"""用paramiko SSH到Kali，再从Kali SSH到EVE-NG"""
import paramiko
import sys

WINDOWS_KEY = r"C:\Users\qq110\.ssh\id_rsa"

def ssh_to_kali():
    transport = paramiko.Transport(("192.168.73.129", 22))
    pkey = paramiko.RSAKey.from_private_key_file(WINDOWS_KEY)
    transport.connect(username="kali", pkey=pkey)
    client = paramiko.SSHClient()
    client.set_transport(transport)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return client

def ssh_from_kali_to_eve(kali_client, cmd, password=None):
    """在Kali上执行ssh命令到EVE-NG"""
    if password:
        full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no {cmd}"
    else:
        full_cmd = f"ssh -o StrictHostKeyChecking=no {cmd}"
    stdin, stdout, stderr = kali_client.exec_command(full_cmd, timeout=30)
    return stdout.read().decode('utf-8', errors='replace')

client = ssh_to_kali()
print("SSH到Kali成功\n")

# 测试Kali到EVE连通
print("[1] Kali到EVE连通性")
out = ssh_from_kali_to_eve(client, "root@192.168.73.130 'hostname'")
print(f"直接ssh结果: {out[:100]}")

# 试试EVE密码
for pwd in ["eve", "root", "password"]:
    out = ssh_from_kali_to_eve(client,
        f"-o StrictHostKeyChecking=no -o ConnectTimeout=5 'root@192.168.73.130' 'hostname; uptime'",
        password=pwd
    )
    print(f"密码={pwd}: {out[:100]}")
    if "permission" not in out.lower()[:30] and "failed" not in out.lower()[:30]:
        print(f"  ✅ 成功!")
        break

# 成功后的命令
print("\n[2] 查看QEMU进程")
out = ssh_from_kali_to_eve(client,
    f"-o StrictHostKeyChecking=no 'root@192.168.73.130' 'ps aux | grep -i qemu | grep -v grep | head -20'",
    password="eve"
)
print(out)

print("\n[3] 查看华为AR相关进程")
out = ssh_from_kali_to_eve(client,
    f"-o StrictHostKeyChecking=no 'root@192.168.73.130' 'ps aux | grep -i AR1k | grep -v grep'",
    password="eve"
)
print(out or "无进程")

print("\n[4] 查看实验目录")
out = ssh_from_kali_to_eve(client,
    f"-o StrictHostKeyChecking=no 'root@192.168.73.130' 'ls /opt/unetlab/tmp/ 2>/dev/null | head -20'",
    password="eve"
)
print(out)

print("\n[5] 查看华为AR镜像文件")
out = ssh_from_kali_to_eve(client,
    f"-o StrictHostKeyChecking=no 'root@192.168.73.130' 'find /opt/unetlab -name \"*huawei*\" -o -name \"*AR1*\" 2>/dev/null | head -20'",
    password="eve"
)
print(out)

print("\n[6] 查看QEMU日志")
out = ssh_from_kali_to_eve(client,
    f"-o StrictHostKeyChecking=no 'root@192.168.73.130' 'tail -50 /var/log/libvirt/qemu/*.log 2>/dev/null || journalctl -u qemu-guest-agent --no-pager -n 30 2>/dev/null || cat /var/log/syslog 2>/dev/null | grep -i qemu | tail -20'",
    password="eve"
)
print(out[:500])

client.close()
print("完成!")
