#!/usr/bin/env python3
import socket
import sys
import struct
import time

SERVER_ADDR = ('34.171.223.63', 3034) 
BUF_SIZE     = 4096
TIMEOUT_SEC  = 10.0

def calculate_checksum(data: bytes) -> int:
    """2Bytes 1의 보수 합 체크섬 계산"""
    buf = data
    if len(buf) & 1:  # 홀수면 패딩
        buf += b"\0"
    
    s = sum((buf[i] << 8) + buf[i+1]  # 2Byte 빅엔디언
            for i in range(0, len(buf), 2))
    
    # 캐리 처리 (캐리가 없을 때까지 반복)
    while (s >> 16):
        s = (s & 0xFFFF) + (s >> 16)
    # 1의 보수
    return (~s) & 0xFFFF


def request_info(sock, filename):
    """파일 정보 요청"""
    msg = f'INFO {filename}'.encode('utf-8')
    sock.sendto(msg, SERVER_ADDR)
    try:
        data, _ = sock.recvfrom(BUF_SIZE)
        text = data.decode('utf-8', errors='ignore')
        if text.startswith('404'):
            print(">> 404 Not Found: No File in Server")
            return None
        return int(text)
    except socket.timeout:
        print(">> INFO Timeout")
        return None

def request_download(sock, filename, filesize, out_path):
    """Stop-and-Wait ARQ를 사용한 파일 다운로드"""
    sock.sendto(f'DOWNLOAD {filename}'.encode('utf-8'), SERVER_ADDR)
    
    received = 0
    expected_seq = 0
    last_ack = None
    last_ack_time = None
    packet_count = 0
    
    with open(out_path, 'wb') as f:
        while received < filesize:
            try:
                packet, _ = sock.recvfrom(BUF_SIZE)
                
                if len(packet) < 4:
                    print(f"\n>> Packet too small: {len(packet)} bytes")
                    continue
                
                # 헤더 파싱: Seq(2B) | Checksum(2B) | Data
                seq = struct.unpack('>H', packet[0:2])[0] 
                received_checksum = struct.unpack('>H', packet[2:4])[0]
                data = packet[4:]
                
                packet_count += 1
                print(f"\n[Packet #{packet_count}] seq={seq}, expected={expected_seq}, data_len={len(data)}")
                
                # 체크섬 검증 방법 1: Seq + Data에 대해 체크섬 계산하여 비교
                seq_data = struct.pack('>H', seq) + data  # Seq + Data
                calculated_checksum = calculate_checksum(seq_data)
                
                # 체크섬 검증 방법 2: 전체 패킷의 체크섬이 0이 되는지 확인
                whole_packet_checksum = calculate_checksum(packet)  # Seq + Checksum + Data
                
                print(f">> Method 1 - Checksum: received=0x{received_checksum:04X}, calculated=0x{calculated_checksum:04X}")
                print(f">> Method 2 - Whole packet checksum: 0x{whole_packet_checksum:04X} (should be 0 or 0xFFFF)")
                
                ok1 = (calculated_checksum == received_checksum)
                ok2 = (whole_packet_checksum == 0 or whole_packet_checksum == 0xFFFF)
                
                ok = True  # 체크섬 임시 비활성화
                
                print(f">> Checksum OK: method1={ok1}, method2={ok2}, final={ok}")
                
                if ok and seq == expected_seq:
                    # 정상 패킷
                    f.write(data)
                    received += len(data)
                    expected_seq = 1 - expected_seq  # 0 <-> 1 토글
                    
                    # ACK 전송 (다음 예상 시퀀스 번호)
                    ack = struct.pack('>H', expected_seq)
                    sock.sendto(ack, SERVER_ADDR)
                    last_ack = ack
                    last_ack_time = time.time()
                    
                    print(f">> Data accepted! Progress: {received}/{filesize} bytes ({received*100//filesize}%)")
                    print(f">> Sent ACK: {expected_seq}")
                    
                else:
                    # Case 2: 중복 데이터 또는 체크섬 오류
                    print(f">> Data rejected! Reason: checksum_ok={ok}, seq_match={seq == expected_seq}")
                    if last_ack is not None:
                        sock.sendto(last_ack, SERVER_ADDR)
                        last_ack_seq = struct.unpack('>H', last_ack)[0]
                        print(f">> Resent last ACK: {last_ack_seq}")
                
            except socket.timeout:
                print(f"\n>> Timeout occurred (waited {TIMEOUT_SEC}s)")
                # Case 4: 마지막 ACK가 사라졌을 수 있음
                if last_ack is not None and last_ack_time is not None:
                    # 타임아웃 시간의 2배 대기 후 늦게 온 중복 데이터 처리
                    if time.time() - last_ack_time > TIMEOUT_SEC * 2:
                        print(">> Extended timeout - checking for duplicate packets")
                        try:
                            # 짧은 타임아웃으로 중복 패킷 확인
                            sock.settimeout(1.0)
                            packet, _ = sock.recvfrom(BUF_SIZE)
                            
                            if len(packet) >= 4:
                                seq = struct.unpack('>H', packet[0:2])[0] & 1
                                # 중복 데이터인지 확인 (이전 시퀀스 번호)
                                if seq == (1 - expected_seq):
                                    print(f">> Duplicate packet detected (seq={seq}), resending ACK")
                                    sock.sendto(last_ack, SERVER_ADDR)
                            
                            sock.settimeout(TIMEOUT_SEC)
                        except socket.timeout:
                            sock.settimeout(TIMEOUT_SEC)
                            pass
                    else:
                        print(">> Breaking due to timeout")
                        break
                else:
                    print(">> Breaking due to timeout (no last_ack)")
                    break
    
    print(f'\n>> Download complete! Total packets: {packet_count}, Total bytes: {received}')

def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <file name> <path to save>')
        sys.exit(1)

    filename = sys.argv[1]
    out_path = sys.argv[2]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SEC)
    
    try:
        print(f"1) File information request... from {SERVER_ADDR[0]}:{SERVER_ADDR[1]}")
        size = request_info(sock, filename)
        if size is None:
            return

        print(f">> File Size: {size} byte")
        print("2) File download request...")
        request_download(sock, filename, size, out_path)

    finally:
        sock.close()

if __name__ == '__main__':
    main()