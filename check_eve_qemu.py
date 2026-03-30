# -*- coding: utf-8 -*-
"""通过Kali跳板SSH到EVE-NG检查QEMU进程"""
import paramiko
import sys

KALI_HOST = "192.168.73.129"
KALI_USER = "kali"
# 从Windows SSH key连Kali
WINDOWS_KEY = r"C:\Users\qq110\.ssh\id_rsa"

EVE_HOST = "192.168.73.130"
EVE_USER = "root"

def run_via_jump(cmd, timeout=30):
    """通过Kali跳板执行SSH命令到EVE-NG"""
    # Step1: SSH到Kali
    transport = paramiko.Transport((KALI_HOST, 22))
    pkey = paramiko.RSAKey.from_private_key_file(WINDOWS_KEY)
    transport.connect(username=KALI_USER, pkey=pkey)
    client = paramiko.SSHClient()
    client.set_transport(transport)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Step2: 通过Kali的TCP通道SSH到EVE-NG
    # 需要先在Kali上做SSH key扫描
    stdin, stdout, stderr = client.exec_command(
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {EVE_USER}@{EVE_HOST} '{cmd}' 2>&1",
        timeout=timeout
    )
    output = stdout.read().decode('utf-8', errors='replace')
    transport.close()
    return output

# 尝试用不同密码SSH到EVE
print("[1] 通过Kali跳板ssh到EVE-NG")
EVE_PASSWORDS = ["eve", "root", "password"]

# 先用密码方式尝试
import subprocess
for pwd in EVE_PASSWORDS:
    result = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
         f"{KALI_USER}@{KALI_HOST}",
         f"sshpass -p '{pwd}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE_USER}@{EVE_HOST} 'hostname && uptime && ps aux | grep -i qemu | grep -v grep | wc -l'"],
        capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
    )
    out = result.stdout + result.stderr
    print(f"  密码={pwd}: {out[:200]}")
    if "permission" not in out.lower()[:50] and result.returncode == 0:
        print(f"  ✅ 成功!")
        break

print("\n[2] 查看EVE-NG的QEMU进程（密码=eve）")
import subprocess
result = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
     f"{KALI_USER}@{KALI_HOST}",
     "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 'ps aux | grep -i qemu | grep -v grep | head -20'"],
    capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
)
out = result.stdout + result.stderr
print(out)

print("\n[3] 查看华为AR相关进程")
result2 = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
     f"{KALI_USER}@{KALI_HOST}",
     "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 'ps aux | grep -i ar1k | grep -v grep; ls /opt/unetlab/tmp/ 2>/dev/null | head -10'"],
    capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
)
print(result2.stdout + result2.stderr)

print("\n[4] 查看QEMU启动日志")
result3 = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
     f"{KALI_USER}@{KALI_HOST}",
     "sshpass -p 'eve' ssh -o StrictHostKeyChecking=no root@192.168.73.130 'journalctl -u libvirtd --no-pager -n 30 2>/dev/null; tail -50 /var/log/libvirt/qemu/*.log 2>/dev/null'"],
    capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
)
print(result3.stdout + result3.stderr)

print("\n完成!")
