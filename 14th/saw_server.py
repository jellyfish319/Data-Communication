#!/usr/bin/env python3
import argparse
import socket
import os
import struct
import time

# 2바이트 1의 보수 합 체크섬 계산
def calculate_checksum(data):
    checksum = 0
    # 데이터를 2바이트씩 처리
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            # 빅 엔디안으로 2바이트 읽기
            word = (data[i] << 8) + data[i+1]
        else:
            # 홀수 바이트 처리
            word = data[i] << 8
        checksum += word
        # 캐리 처리
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    # 1의 보수
    return (~checksum) & 0xFFFF

# 데이터 패킷 생성: Seq(2B) | Checksum(2B) | Data
def create_packet(seq_num, data):
    seq_bytes = struct.pack('>H', seq_num)
    # 체크섬은 'Seq+Data'에 대해 계산
    checksum = calculate_checksum(seq_bytes + data)
    checksum_bytes = struct.pack('>H', checksum)
    return seq_bytes + checksum_bytes + data

# ACK 패킷 검증
def verify_ack(packet, expected_ack):
    try:
        if len(packet) != 4:
            return False, -1
        
        # 전체 ACK 패킷에 대한 체크섬 검증
        if calculate_checksum(packet) != 0:
            return False, -1

        ack_num, _ = struct.unpack('>HH', packet)
        
        if ack_num == expected_ack:
            return True, ack_num
        else:
            return False, ack_num
            
    except struct.error:
        return False, -1

# Stop-and-Wait ARQ로 데이터 청크 전송
def send_chunk_saw(sock, client_addr, data, seq_num):
    packet = create_packet(seq_num, data)
    expected_ack = 1 - seq_num
    
    # 최대 5번 재전송
    for attempt in range(5):
        try:
            sock.sendto(packet, client_addr)
            print(f"Server: [Seq={seq_num}] Sending data (Attempt {attempt+1})")
            
            # ACK 대기 (타임아웃 2초)
            sock.settimeout(2.0)
            ack_packet, addr = sock.recvfrom(1024)
            
            if addr == client_addr:
                is_valid, ack_num = verify_ack(ack_packet, expected_ack)
                if is_valid:
                    print(f"Server: [Ack={ack_num}] Received successfully")
                    return True # 성공적으로 ACK 수신
                else:
                    print(f"Server: Invalid ACK received (Expected: {expected_ack}, Got: {ack_num})")
        
        except socket.timeout:
            print(f"Server: [Seq={seq_num}] Timeout occurred")
            continue # 재전송
            
    return False # 전송 실패

# 파일 다운로드 처리
def handle_download(sock, client_addr, filename, file_table, mtu):
    info = file_table.get(filename)
    if not info:
        sock.sendto(b'404 Not Found', client_addr)
        return

    print(f"Server: [{client_addr[0]}:{client_addr[1]}] File download request: {filename}")

    try:
        with open(info['path'], 'rb') as f:
            seq_num = 0
            # 데이터 크기: MTU - 헤더(Seq 2B + Checksum 2B)
            data_size = mtu - 4
            
            while True:
                chunk = f.read(data_size)
                if not chunk:
                    break # 파일 끝
                
                # Stop-and-Wait로 청크 전송
                if not send_chunk_saw(sock, client_addr, chunk, seq_num):
                    print(f"Server: [Seq={seq_num}] Transmission finally failed")
                    return
                
                # 시퀀스 번호 토글 (0 <-> 1)
                seq_num = 1 - seq_num

            # 파일 전송 완료 후 빈 패킷 전송하여 종료 신호 전달
            send_chunk_saw(sock, client_addr, b'', seq_num)
            print(f"Server: {filename} sent successfully")

    except Exception as e:
        print(f"Server: Error during file handling: {e}")

# 파일 정보 요청 처리
def handle_info(sock, client_addr, filename, file_table):
    info = file_table.get(filename)
    response = str(info['size']).encode('utf-8') if info else b'404 Not Found'
    sock.sendto(response, client_addr)

def main():
    parser = argparse.ArgumentParser(description="Stop-and-Wait ARQ File Server")
    parser.add_argument('--port', type=int, default=10000, help="Server port")
    parser.add_argument('--dir', type=str, default='.', help="Directory of files to serve")
    parser.add_argument('--mtu', type=int, default=1500, help="Maximum Transmission Unit")
    args = parser.parse_args()

    # 서비스할 파일 목록 생성
    file_table = {f: {'path': os.path.join(args.dir, f), 'size': os.path.getsize(os.path.join(args.dir, f))}
                  for f in os.listdir(args.dir) if os.path.isfile(os.path.join(args.dir, f))}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', args.port))
    print(f"Server: Stop-and-Wait server started (Port: {args.port}, MTU: {args.mtu})")

    try:
        while True:
            sock.settimeout(None) # 새 요청을 무한 대기
            data, client_addr = sock.recvfrom(4096)
            message = data.decode('utf-8', errors='ignore').strip()
            
            print(f"Server: [{client_addr[0]}:{client_addr[1]}] Message received: {message}")
            
            if message.startswith('INFO'):
                _, filename = message.split(' ', 1)
                handle_info(sock, client_addr, filename, file_table)
            elif message.startswith('DOWNLOAD'):
                _, filename = message.split(' ', 1)
                handle_download(sock, client_addr, filename, file_table, args.mtu)
            else:
                sock.sendto(b'400 Bad Request', client_addr)

    except KeyboardInterrupt:
        print("\nServer: Shutting down server")
    finally:
        sock.close()

if __name__ == '__main__':
    main() 