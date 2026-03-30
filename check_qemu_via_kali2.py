# -*- coding: utf-8 -*-
import subprocess
import sys

KALI = "kali@192.168.73.129"
EVE = "root@192.168.73.130"
KEY_FILE = r"C:\Users\qq110\.ssh\id_rsa"

def run(cmd):
    """在Kali上执行命令，返回stdout"""
    result = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "PasswordAuthentication=no",
         "-i", KEY_FILE, KALI, cmd],
        capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
    )
    return result.stdout + result.stderr

print("[1] 从Kali测试到EVE-NG的连通性")
out = run(f"ping -c 2 -W 1 {EVE_HOST := '192.168.73.130'}")
print(out[:300])

print("\n[2] 尝试ssh到EVE-NG（无密码方式，用密钥）")
# 先确保Kali有到EVE的SSH密钥
run(f"ssh-keyscan -H {EVE_HOST} >> ~/.ssh/known_hosts 2>/dev/null")
out = run(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {EVE} 'hostname && uptime' 2>&1")
print(f"无密码ssh结果:\n{out[:300]}")

if "permission" in out.lower() or "password" in out.lower()[:50]:
    print("\n[3] 用密码尝试ssh到EVE")
    for pwd in ["eve", "root", "password", "admin"]:
        result = subprocess.run(
            ["sshpass", "-p", pwd, "ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5", f"{EVE.split('@')[1]}@{EVE.split('@')[0]}", "hostname && uptime"],
            capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace'
        )
        out2 = result.stdout + result.stderr
        print(f"  密码={pwd}: {out2[:100]}")
        if "permission" not in out2.lower()[:50] and out2.strip():
            print(f"  ✅ 成功! 输出: {out2[:200]}")
            break
