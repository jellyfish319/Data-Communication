#!/usr/bin/env python3
import socket
import sys
import os
import struct
import time

# GBN 상수
SEQ_NUM_RANGE = 16  # 0-15

# 2바이트 1의 보수 합 체크섬 계산
def calculate_checksum(data):
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1] if i + 1 < len(data) else data[i] << 8
        checksum += word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    return (~checksum) & 0xFFFF

# 수신된 데이터 패킷 검증
def verify_packet(packet):
    try:
        if len(packet) < 4: return False, -1, b''
        
        # Unpack header first to get seq_num for logging, even on failure
        seq_num, _ = struct.unpack('>HH', packet[:4])

        # Checksum validation on the entire packet. A result of 0 means it's valid.
        if calculate_checksum(packet) != 0:
            return False, seq_num, b''
            
        # If valid, extract data
        data = packet[4:]
        return True, seq_num, data
        
    except (struct.error, TypeError):
        return False, -1, b''

# ACK 패킷 생성
def create_ack_packet(ack_num):
    ack_bytes = struct.pack('>H', ack_num)
    checksum = calculate_checksum(ack_bytes)
    return ack_bytes + struct.pack('>H', checksum)

# 파일 정보 요청
def request_info(sock, server_addr, filename):
    sock.sendto(f'INFO {filename}'.encode('utf-8'), server_addr)
    try:
        sock.settimeout(3.0)
        data, _ = sock.recvfrom(1024)
        size_str = data.decode('utf-8')
        if size_str.isdigit():
            return int(size_str)
        else:
            print(f"Client: Server error: {size_str}")
            return None
    except socket.timeout:
        print("Client: File info request timeout")
        return None

# Go-Back-N ARQ로 파일 다운로드
def request_download_gbn(sock, server_addr, filename, out_path, filesize):
    sock.sendto(f'DOWNLOAD {filename}'.encode('utf-8'), server_addr)
    
    expected_seq_num = 0
    received_bytes = 0
    start_time = time.time()
    
    with open(out_path, 'wb') as f:
        while True:
            try:
                sock.settimeout(5.0) # 서버 응답 대기
                packet, addr = sock.recvfrom(2048)
                if addr != server_addr: continue

                is_valid, seq_num, data = verify_packet(packet)

                if is_valid and seq_num == expected_seq_num:
                    # 올바른 순서의 패킷 수신
                    if not data: # 전송 종료
                        end_time = time.time()
                        print("\nClient: File transfer complete")

                        total_time = end_time - start_time
                        if total_time > 0 and filesize > 0:
                            throughput_bps = (filesize * 8) / total_time
                            print(f"Client: Total time: {total_time:.2f} seconds")
                            print(f"Client: Throughput: {throughput_bps:,.0f} bps ({throughput_bps/1_000_000:.2f} Mbps)")

                        ack_packet = create_ack_packet((expected_seq_num + 1) % SEQ_NUM_RANGE)
                        sock.sendto(ack_packet, server_addr)
                        break

                    f.write(data)
                    received_bytes += len(data)
                    print(f"\rClient: [Seq={seq_num}] Received. {received_bytes}/{filesize} bytes downloaded", end='')
                    
                    # 다음 패킷에 대한 누적 ACK 전송
                    ack_packet = create_ack_packet((expected_seq_num + 1) % SEQ_NUM_RANGE)
                    sock.sendto(ack_packet, server_addr)
                    expected_seq_num = (expected_seq_num + 1) % SEQ_NUM_RANGE
                else:
                    if not is_valid:
                        print(f"\nClient: [Seq={seq_num}] Corrupted packet received. Ignored.")
                    else:
                        print(f"\nClient: [Seq={seq_num}] Out-of-order packet received (Expected: {expected_seq_num}). Ignored.")
                    
                    # 마지막으로 확인된 ACK 재전송
                    ack_packet = create_ack_packet(expected_seq_num)
                    sock.sendto(ack_packet, server_addr)

            except socket.timeout:
                print("\nClient: Server response timeout. Exiting.")
                return
    
    # 최종 ACK 재전송 (서버의 대기 시간에 맞춰)
    print("Client: Sending final confirmation ACKs...")
    for _ in range(3):
        ack_packet = create_ack_packet(expected_seq_num)
        sock.sendto(ack_packet, server_addr)
        time.sleep(0.5)
    print("Client: Client shutting down.")


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <server_ip> <server_port> <filename> <out_path>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    out_path = sys.argv[4]
    server_addr = (server_ip, server_port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        filesize = request_info(sock, server_addr, filename)
        if filesize is None: return

        print(f"Client: File size: {filesize} bytes. Starting GBN download.")
        request_download_gbn(sock, server_addr, filename, out_path, filesize)

    except Exception as e:
        print(f"Client: An error occurred: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    main() 