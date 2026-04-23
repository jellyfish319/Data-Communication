import socket
import argparse
import os
import sys

def load_files(root_dir):

    files = {}
    for entry in os.scandir(root_dir):
        if entry.is_file():
            files[entry.name] = {
                'path': entry.path,
                'size': os.path.getsize(entry.path)
            }
    return files

def serve(bind_addr, bind_port, root_dir, chunk_size):
    files = load_files(root_dir)
    if not files:
        print(f"[!] {root_dir}에 전송 가능한 파일이 없습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Serving directory: {root_dir}")
    for name, info in files.items():
        print(f"    {name}  ({info['size']} bytes)")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_addr, bind_port))
    print(f"[+] UDP 서버 시작: {bind_addr}:{bind_port}, chunk_size={chunk_size}")

    try:
        while True:
            data, client = sock.recvfrom(2048)
            text = data.decode('utf-8', errors='ignore').strip()
            print(f"[REQ] {client} → {text}")

            parts = text.split(maxsplit=1)
            if len(parts) != 2:
                sock.sendto(b'400 Bad Request', client)
                continue

            cmd, filename = parts[0].upper(), parts[1]
            info = files.get(filename)

            if cmd == 'INFO':
                if not info:
                    sock.sendto(b'404 Not Found', client)
                else:
                    sock.sendto(str(info['size']).encode('utf-8'), client)

            elif cmd == 'DOWNLOAD':
                if not info:
                    sock.sendto(b'404 Not Found', client)
                else:
                    with open(info['path'], 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            sock.sendto(chunk, client)
                    print(f"[SENT] {filename} → {client}")

            else:
                sock.sendto(b'400 Bad Request', client)

    except KeyboardInterrupt:
        print("\n[+] 서버를 종료합니다.")
    finally:
        sock.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="DCFT1-style UDP File Server")
    p.add_argument('--addr',  default='0.0.0.0',
                   help='바인딩할 주소 (기본: 0.0.0.0)')
    p.add_argument('--port',  type=int, default=3034,
                   help='포트 번호 (기본: 3034)')
    p.add_argument('--dir',   required=True,
                   help='전송할 파일이 들어있는 디렉터리')
    p.add_argument('--mtu',   type=int, default=1500,
                   help='전송 청크 최대 크기 (기본: 1500)')
    args = p.parse_args()

    serve(args.addr, args.port, args.dir, args.mtu)
