# -*- coding: utf-8 -*-
"""华为AR1K console交互测试 - 发命令看响应"""
import socket, time, sys

def console_cmd(host, port, cmd, wait=5):
    """发送命令到console并读取响应"""
    s = socket.socket()
    s.settimeout(wait + 3)
    try:
        s.connect((host, port))
        # 初始唤醒
        s.send(b"\r\n")
        time.sleep(2)
        # 清空初始输出
        try:
            s.recv(8192)
        except: pass
        
        # 发送命令
        s.send(f"{cmd}\r\n".encode())
        time.sleep(wait)
        
        # 读取所有响应
        data = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
            except socket.timeout: break
        
        s.close()
        return data
    except Exception as e:
        return f"Error: {e}".encode()

# 华为实验console端口
ports = {
    "R1": 32769,
    "R2": 32770,
    "R3": 32771,
}

print("=== 测试华为AR1K Console命令响应 ===")
for name, port in ports.items():
    print(f"\n--- {name} (port={port}) ---")
    
    # 先发回车看提示符
    data = console_cmd('192.168.73.130', port, "")
    text = data.decode('utf-8', errors='replace')
    lines = [l for l in text.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip()]
    print(f"发回车后: {len(text)} 字节, {len(lines)} 行")
    for l in lines[:15]:
        print(f"  {l[:120]}")
    
    # 发 ctrl+C 中断可能存在的boot过程
    data2 = console_cmd('192.168.73.130', port, "\x03", wait=3)
    text2 = data2.decode('utf-8', errors='replace')
    lines2 = [l for l in text2.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip()]
    if lines2:
        print(f"发Ctrl+C后: {len(text2)} 字节:")
        for l in lines2[:10]:
            print(f"  {l[:120]}")
    
    # 写文件
    with open(f'C:\\Users\\qq110\\.openclaw\\workspace\\.cache\\huawei_{name.lower()}_console.txt', 'w', encoding='utf-8', errors='replace') as f:
        f.write(text)

print("\n完成!")
