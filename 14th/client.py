#!/usr/bin/env python3
import socket
import sys
import os

SERVER_ADDR = ('34.171.223.63', 3034) 
BUF_SIZE     = 4096
TIMEOUT_SEC  = 3.0

def request_info(sock, filename):
    msg = f'INFO {filename}'.encode('utf-8')
    sock.sendto(msg, SERVER_ADDR)
    try:
        data, _ = sock.recvfrom(BUF_SIZE)
        text = data.decode('utf-8', errors='ignore')
        if text.startswith('404'):
            print(">> 서버에 해당 파일이 없습니다.")
            return None
        return int(text)
    except socket.timeout:
        print(">> INFO 응답 타임아웃")
        return None

def request_download(sock, filename, filesize, out_path):
    sock.sendto(f'DOWNLOAD {filename}'.encode('utf-8'), SERVER_ADDR)
    received = 0
    with open(out_path, 'wb') as f:
        while received < filesize:
            try:
                chunk, _ = sock.recvfrom(BUF_SIZE)
            except socket.timeout:
                print(">> 다운로드 중 타임아웃")
                break
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)
            print(f'\r다운받은 {received}/{filesize} 바이트', end='')
    print('\n>> 다운로드 완료')

def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <파일명> <저장할_경로>')
        sys.exit(1)

    filename = sys.argv[1]
    out_path = sys.argv[2]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SEC)
    try:
        print("1) 파일 정보 요청 중...")
        size = request_info(sock, filename)
        if size is None:
            return

        print(f">> 파일 크기: {size} 바이트")
        print("2) 파일 다운로드 요청 중...")
        request_download(sock, filename, size, out_path)

    finally:
        sock.close()

if __name__ == '__main__':
    main()
