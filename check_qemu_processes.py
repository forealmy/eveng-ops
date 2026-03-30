# -*- coding: utf-8 -*-
"""检查华为AR1K的QEMU进程状态"""
import paramiko
import time

EVE_HOST = "192.168.73.130"
EVE_USER = "root"
EVE_PASSWORD = "eve"  # EVE-NG默认root密码

def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(EVE_HOST, username=EVE_USER, password=EVE_PASSWORD, timeout=10)
    return client

def check_qemu_processes(client, lab_name):
    """查找实验对应的QEMU进程"""
    # 先找到实验对应的虚拟机的UUID
    # EVE-NG QEMU进程通常包含节点信息
    cmd = f"ps aux | grep -i 'qemu.*huawei\\|qemu.*{lab_name}' | grep -v grep"
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode()
    print(f"=== QEMU进程 (关键词huawei/lab) ===")
    print(output or "无结果")
    print()

    # 列出所有 qemu-kvm / qemu-system 进程
    cmd2 = "ps aux | grep -i 'qemu' | grep -v grep"
    stdin, stdout, stderr = client.exec_command(cmd2)
    output2 = stdout.read().decode()
    print(f"=== 所有QEMU进程 ===")
    print(output2 or "无QEMU进程")
    print()

    # 查看实验目录
    cmd3 = f"find /opt/unetlab/tmp/ -name '*.qcow2' -o -name '*.img' 2>/dev/null | head -20"
    stdin, stdout, stderr = client.exec_command(cmd3)
    output3 = stdout.read().decode()
    print(f"=== 磁盘镜像文件 ===")
    print(output3 or "无镜像文件")
    print()

    # 查看特定实验的节点进程
    cmd4 = "ps aux | grep -i 'huaweiar\\|h3cvsr\\|AR1000' | grep -v grep"
    stdin, stdout, stderr = client.exec_command(cmd4)
    output4 = stdout.read().decode()
    print(f"=== 华为/H3C相关进程 ===")
    print(output4 or "无")
    print()

    # 看QEMU启动日志
    cmd5 = "ls -la /opt/unetlab/tmp/ 2>/dev/null | head -20"
    stdin, stdout, stderr = client.exec_command(cmd5)
    output5 = stdout.read().decode()
    print(f"=== /opt/unetlab/tmp/ ===")
    print(output5 or "目录不存在")

def check_console_logs(client, node_name="R1"):
    """查看节点控制台日志"""
    # EVE-NG console日志通常在 /var/tmp
    cmds = [
        f"ls -la /var/tmp/ | grep -i {node_name.lower()} | head -10",
        f"cat /var/tmp/il_{node_name.lower()}* 2>/dev/null | tail -50",
        f"dmesg | grep -i qemu | tail -20",
    ]
    for cmd in cmds:
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        if out.strip():
            print(f"[{cmd[:50]}]")
            print(out)
            print()

try:
    print("SSH连接到EVE-NG服务器...")
    client = ssh_connect()
    print("已连接!\n")

    check_qemu_processes(client, "OSPF_Huawei_Lab")
    print("\n--- 华三实验 ---")
    check_qemu_processes(client, "OSPF_H3C_Lab")

    client.close()
    print("断开连接")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
