# -*- coding: utf-8 -*-
"""交互式telnet到H3C节点，发送命令看实际输出"""
import socket
import time
import sys

def interact_telnet(host, port, cmds, timeout=5):
    """telnet交互：发送命令并读取所有响应"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        # 等待初始启动输出
        time.sleep(3)
        data = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                break
        boot_output = data.decode('ascii', errors='replace')
        print(f"    [初始输出 {len(boot_output)}字节]:")
        for line in boot_output.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            if line.strip():
                print(f"      {line[:120]}")
        
        # 发送命令
        results = []
        for cmd in cmds:
            s.send(f"{cmd}\r\n".encode())
            time.sleep(2)
            data = b""
            while True:
                try:
                    chunk = s.recv(8192)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
            output = data.decode('ascii', errors='replace')
            print(f"\n    [{cmd}]:")
            for line in output.replace('\r\n', '\n').replace('\r', '\n').split('\n')[-15:]:  # 只打印最后15行
                if line.strip():
                    print(f"      {line[:120]}")
            results.append(output)
        
        s.close()
        return boot_output, results
    except Exception as e:
        return f"Error: {e}", []

# 测试H3C R1
print("=== 交互telnet到H3C R1 (192.168.73.130:32769) ===")
boot, res = interact_telnet('192.168.73.130', 32769, ['?', 'display version', 'system-view', 'display current-configuration'])

print("\n=== 测试华为R1 (192.168.73.130:32769) - 注意端口冲突 ===")
# 注意：华为和H3C的telnet端口都是32769开始的，不能同时测
# 只测H3C

print("\n完成!")
