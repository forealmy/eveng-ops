# -*- coding: utf-8 -*-
"""读取华为AR1K console - 长时间读取"""
import socket
import time

def read_console_long(host, port, wait_sec=15):
    s = socket.socket()
    s.settimeout(wait_sec + 5)
    s.connect((host, port))
    s.settimeout(2)
    
    all_data = b""
    # 持续读取 wait_sec 秒
    start = time.time()
    while time.time() - start < wait_sec:
        try:
            chunk = s.recv(4096)
            if chunk:
                all_data += chunk
                print(f"  +{len(chunk)} bytes at t={time.time()-start:.1f}s", flush=True)
            else:
                break
        except socket.timeout:
            # No data available, wait a bit
            time.sleep(0.5)
            continue
    
    s.close()
    return all_data

print("=== 华为 R1 console (32769) 长时间读取 ===")
data = read_console_long('192.168.73.130', 32769, wait_sec=15)
print(f"\n总接收: {len(data)} 字节")
print("内容预览:")
text = data.decode('utf-8', errors='replace')
for i, line in enumerate(text.split('\n')):
    if line.strip():
        print(f"  [{i:3d}] {line[:120]}")
        if i > 50:
            print("  ... (更多)")
            break

print("\n\n=== 华为 R2 console (32770) ===")
data2 = read_console_long('192.168.73.130', 32770, wait_sec=15)
print(f"\n总接收: {len(data2)} 字节")
text2 = data2.decode('utf-8', errors='replace')
for i, line in enumerate(text2.split('\n')):
    if line.strip():
        print(f"  [{i:3d}] {line[:120]}")
        if i > 30:
            print("  ...")
            break
