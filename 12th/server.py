#!/usr/bin/env python3
import argparse
import socket
import os
import sys

# --mtu 플래그 정의 (기본값 1500)
parser = argparse.ArgumentParser(description="UDP 파일 서버")
parser.add_argument('--mtu', type=int, default=1500, help='전송 단위 크기 (바이트)')
parser.add_argument('--port', type=int, default=3034, help='서버 바인드 포트')
FLAGS = parser.parse_args()

# 서비스 가능한 파일 목록 초기화
BASE_DIR = os.getcwd()
file_table = {}
for fname in os.listdir(BASE_DIR):
    path = os.path.join(BASE_DIR, fname)
    if os.path.isfile(path):
        file_table[fname] = {
            'path': path,
            'size': os.path.getsize(path)
        }

def handle_info(sock, addr, filename):
    info = file_table.get(filename)
    if info:
        sock.sendto(str(info['size']).encode('utf-8'), addr)
    else:
        sock.sendto(b'404 Not Found', addr)

def handle_download(sock, addr, filename):
    info = file_table.get(filename)
    if not info:
        sock.sendto(b'404 Not Found', addr)
        return
    with open(info['path'], 'rb') as f:
        while True:
            chunk = f.read(FLAGS.mtu)
            if not chunk:
                break
            sock.sendto(chunk, addr)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', FLAGS.port))
    print(f"UDP 파일 서버 시작 (포트 {FLAGS.port}, MTU {FLAGS.mtu})")
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            text = data.decode('utf-8', errors='ignore').strip()
            if text.startswith('INFO '):
                _, filename = text.split(' ', 1)
                handle_info(sock, addr, filename)
            elif text.startswith('DOWNLOAD '):
                _, filename = text.split(' ', 1)
                handle_download(sock, addr, filename)
            else:
                sock.sendto(b'400 Bad Request', addr)
    except KeyboardInterrupt:
        print("\n서버 종료")
    finally:
        sock.close()

if __name__ == '__main__':
    main()
