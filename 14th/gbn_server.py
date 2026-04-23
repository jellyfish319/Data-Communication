#!/usr/bin/env python3
import argparse
import socket
import os
import struct
import threading
import time

# GBN 상수
SEQ_NUM_RANGE = 16  # 0-15
WINDOW_SIZE = 8     # Window size N (N < SEQ_NUM_RANGE)
TIMEOUT = 2.0       # Timeout in seconds

# 공유 변수 및 락
base = 0
mutex = threading.Lock()
timer = None

# 2바이트 1의 보수 합 체크섬 계산
def calculate_checksum(data):
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1] if i + 1 < len(data) else data[i] << 8
        checksum += word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    return (~checksum) & 0xFFFF

# 데이터 패킷 생성: Seq(2B) | Checksum(2B) | Data
def create_packet(seq_num, data):
    seq_bytes = struct.pack('>H', seq_num)
    checksum = calculate_checksum(seq_bytes + data)
    checksum_bytes = struct.pack('>H', checksum)
    return seq_bytes + checksum_bytes + data

# ACK 패킷 검증
def verify_ack(packet):
    try:
        if len(packet) != 4: return False, -1
        
        # 전체 ACK 패킷에 대한 체크섬 검증
        if calculate_checksum(packet) != 0:
            return False, -1
            
        ack_num, _ = struct.unpack('>HH', packet)
        return True, ack_num
        
    except struct.error:
        return False, -1

# ACK 수신을 처리하는 스레드 함수
def ack_receiver(sock):
    global base, mutex, timer
    while True:
        try:
            ack_packet, _ = sock.recvfrom(1024)
            is_valid, ack_num = verify_ack(ack_packet)

            if is_valid:
                with mutex:
                    # 유효한 누적 ACK 수신 시 base 업데이트
                    if (base < ack_num <= base + WINDOW_SIZE) or \
                       (base + WINDOW_SIZE >= SEQ_NUM_RANGE and (ack_num < base or ack_num > base)): # 순환 고려
                        print(f"Server: [Ack={ack_num}] received. Base: {base} -> {ack_num}")
                        base = ack_num
                        if timer and timer.is_alive():
                            timer.cancel()
            else:
                print("Server: Corrupted ACK received")
        except Exception:
            break # 메인 스레드 종료 시

# 파일 다운로드 처리 (Go-Back-N)
def handle_download_gbn(sock, client_addr, filename, file_table, mtu):
    global base, mutex, timer
    info = file_table.get(filename)
    if not info:
        sock.sendto(b'404 Not Found', client_addr)
        return

    print(f"Server: [{client_addr[0]}:{client_addr[1]}] GBN file download request: {filename}")
    
    # ACK 수신 스레드 시작
    receiver_thread = threading.Thread(target=ack_receiver, args=(sock,))
    receiver_thread.daemon = True
    receiver_thread.start()

    packets = []
    seq_num = 0
    data_size = mtu - 4 # Seq(2B) + Checksum(2B)
    with open(info['path'], 'rb') as f:
        while True:
            chunk = f.read(data_size)
            if not chunk: break
            packets.append(create_packet(seq_num, chunk))
            seq_num = (seq_num + 1) % SEQ_NUM_RANGE
    
    # 전송 완료를 알리는 빈 데이터 패킷 추가
    packets.append(create_packet(seq_num, b''))

    base = 0
    next_seq_num = 0
    total_packets = len(packets)

    while base < total_packets:
        with mutex:
            # 윈도우 내의 모든 패킷 전송
            while next_seq_num < base + WINDOW_SIZE and next_seq_num < total_packets:
                sock.sendto(packets[next_seq_num], client_addr)
                print(f"Server: [Seq={next_seq_num % SEQ_NUM_RANGE}] Sending data")
                next_seq_num += 1

            # 타이머 설정 (윈도우에 전송된 패킷이 있고, 타이머가 돌고있지 않을 때)
            if base < next_seq_num and (timer is None or not timer.is_alive()):
                def timeout_handler():
                    print(f"Server: [Base={base % SEQ_NUM_RANGE}] Timeout occurred. Starting retransmission")
                    with mutex:
                        # 윈도우 내 모든 패킷 재전송
                        for i in range(base, next_seq_num):
                            sock.sendto(packets[i], client_addr)
                            print(f"Server: [Seq={i % SEQ_NUM_RANGE}] Resending data")

                timer = threading.Timer(TIMEOUT, timeout_handler)
                timer.start()
        
        time.sleep(0.01) # CPU 사용량 조절

    if timer and timer.is_alive():
        timer.cancel()
    print(f"Server: {filename} sent successfully")
    time.sleep(2 * TIMEOUT) # 마지막 ACK 유실 대비

# 파일 정보 요청 처리
def handle_info(sock, client_addr, filename, file_table):
    info = file_table.get(filename)
    response = str(info['size']).encode('utf-8') if info else b'404 Not Found'
    sock.sendto(response, client_addr)

def main():
    parser = argparse.ArgumentParser(description="Go-Back-N ARQ File Server")
    parser.add_argument('--port', type=int, default=20000, help="Server port")
    parser.add_argument('--dir', type=str, default='.', help="Directory of files to serve")
    parser.add_argument('--mtu', type=int, default=1500, help="Maximum Transmission Unit")
    args = parser.parse_args()

    file_table = {f: {'path': os.path.join(args.dir, f), 'size': os.path.getsize(os.path.join(args.dir, f))}
                  for f in os.listdir(args.dir) if os.path.isfile(os.path.join(args.dir, f))}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', args.port))
    print(f"Server: Go-Back-N server started (Port: {args.port}, MTU: {args.mtu})")

    try:
        while True:
            data, client_addr = sock.recvfrom(4096)
            message = data.decode('utf-8', errors='ignore').strip()
            print(f"Server: [{client_addr[0]}:{client_addr[1]}] Message received: {message}")
            
            if message.startswith('INFO'):
                handle_info(sock, client_addr, filename, file_table)
            elif message.startswith('DOWNLOAD'):
                _, filename = message.split(' ', 1)
                download_thread = threading.Thread(target=handle_download_gbn, args=(sock, client_addr, filename, file_table, args.mtu))
                download_thread.start()
            else:
                sock.sendto(b'400 Bad Request', client_addr)

    except KeyboardInterrupt:
        print("\nServer: Shutting down server")
    finally:
        sock.close()

if __name__ == '__main__':
    main() 