# -*- coding: utf-8 -*-
"""发送回车触发华为console输出"""
import socket, time, sys

def interact(host, port):
    s = socket.socket()
    s.settimeout(10)
    s.connect((host, port))
    
    # 清空缓冲区
    time.sleep(1)
    try:
        s.recv(8192)
    except:
        pass
    
    # 发回车
    print("发送回车...")
    s.send(b"\r\n")
    
    # 等待响应
    time.sleep(5)
    data = b""
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            print(f"收到 {len(chunk)} 字节")
        except socket.timeout:
            break
    
    s.close()
    return data

# 华为R1 (当前端口可能与H3C冲突，先试R1)
print("=== 测试华为R1 (32769) ===")
data = interact('192.168.73.130', 32769)
print(f"\n总: {len(data)} 字节")

# 写到文件，避免编码问题
with open(r'C:\Users\qq110\.openclaw\workspace\.cache\huawei_console_r1.txt', 'w', encoding='utf-8', errors='replace') as f:
    f.write(data.decode('utf-8', errors='replace'))
print("已写入缓存文件")

# 再试华为R2 (32770)
print("\n=== 测试华为R2 (32770) ===")
data2 = interact('192.168.73.130', 32770)
print(f"\n总: {len(data2)} 字节")
with open(r'C:\Users\qq110\.openclaw\workspace\.cache\huawei_console_r2.txt', 'w', encoding='utf-8', errors='replace') as f:
    f.write(data2.decode('utf-8', errors='replace'))
print("已写入缓存文件")
