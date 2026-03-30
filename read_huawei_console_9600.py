# -*- coding: utf-8 -*-
"""以9600波特率读取华为AR1K console"""
import sys
import socket
import time

def telnet_9600(host, port, timeout=10):
    """读取华为AR1K console（9600波特率）"""
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        # 等待数据
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
        s.close()
        return data
    except Exception as e:
        return f"Error: {e}".encode()

# 华为实验节点
# R1:32769, R2:32770, R3:32771
for port in [32769, 32770, 32771]:
    print(f"\n=== 华为R1 端口{port} (9600波特率) ===")
    data = telnet_9600('192.168.73.130', port)
    text = data.decode('ascii', errors='replace')
    lines = [l for l in text.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip()]
    print(f"共收到 {len(text)} 字节，{len(lines)} 行")
    for l in lines[:30]:
        print(f"  {l[:120]}")
    if not lines:
        print("  无输出（可能需要等待更长时间或节点未运行）")

print("\n完成!")
