import socket
import struct
import time
import random

# 클라이언트 설정
SERVER_IP = '34.173.78.46'   # VM 서버의 IP로 설정
SERVER_PORT = 3034

def go_back_n_client(filename, loss_rate=0.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    file = open(filename, 'wb')

    try:
        # 파일 정보 요청
        info_msg = f"INFO {filename}".encode('utf-8')
        sock.sendto(info_msg, (SERVER_IP, SERVER_PORT))
        data, _ = sock.recvfrom(1024)
    except socket.timeout:
        print("[클라이언트] 서버 응답 없음 - 종료")
        file.close()
        return

    resp = data.decode('utf-8', errors='ignore')
    if resp.startswith("404"):
        print("[클라이언트] 파일이 존재하지 않습니다.")
        file.close()
        return
    try:
        file_size = int(resp)
    except ValueError:
        print("[클라이언트] 잘못된 파일 크기 정보.")
        file.close()
        return
    print(f"[클라이언트] 파일 크기: {file_size} 바이트")

    # 다운로드 요청
    down_msg = f"DOWNLOAD {filename}".encode('utf-8')
    sock.sendto(down_msg, (SERVER_IP, SERVER_PORT))
    print("[클라이언트] 파일 다운로드 시작...")

    bytes_received = 0
    expected_seq = 0
    start_time = time.time()

    while bytes_received < file_size:
        try:
            packet, _ = sock.recvfrom(1500)
        except socket.timeout:
            print("[클라이언트] 데이터 수신 시간초과 - 서버 응답 없음.")
            break

        if len(packet) < 4:
            continue

        seq_num = struct.unpack('!H', packet[:2])[0]
        recv_checksum = struct.unpack('!H', packet[2:4])[0]
        data = packet[4:]
        # 체크섬 계산
        calc_sum = 0
        temp_packet = packet[:2] + b'\x00\x00' + data
        for i in range(0, len(temp_packet), 2):
            two_bytes = temp_packet[i:i+2]
            if len(two_bytes) < 2:
                two_bytes += b'\x00'
            calc_sum += struct.unpack('!H', two_bytes)[0]
            calc_sum &= 0xffff
        calc_sum = (~calc_sum) & 0xffff
        if calc_sum != recv_checksum:
            print(f"[클라이언트] 패킷 손상됨 (Seq:{seq_num}) - 폐기")
            continue

        if seq_num == expected_seq:
            # 올바른 순서 패킷 수신
            file.write(data)
            bytes_received += len(data)
            expected_seq = (expected_seq + 1) % 16
            print(f"[클라이언트] #{seq_num} 패킷 수신 (크기 {len(data)} bytes)")

            # ACK 전송
            ack_num = expected_seq
            ack_bytes = struct.pack('!H', ack_num)
            ack_sum = (ack_num + 0) & 0xffff
            ack_sum = (~ack_sum) & 0xffff
            ack_checksum = struct.pack('!H', ack_sum)
            ack_packet = ack_bytes + ack_checksum
            if loss_rate > 0 and random.random() < loss_rate:
                print(f"[클라이언트] ACK#{ack_num} 손실시뮬레이션: 전송 생략")
            else:
                sock.sendto(ack_packet, (SERVER_IP, SERVER_PORT))
                print(f"[클라이언트] ACK#{ack_num} 전송")
        else:
            # 순서에 맞지 않는 패킷
            print(f"[클라이언트] 순서 오류 패킷 수신 (Seq:{seq_num}, 기대:{expected_seq})")
            # 아직 expected_seq 못 받았는데 다음 것이 온 경우 또는 중복 패킷
            # -> 현재 기대 번호의 ACK 재전송
            ack_num = expected_seq
            ack_bytes = struct.pack('!H', ack_num)
            ack_sum = (ack_num + 0) & 0xffff
            ack_sum = (~ack_sum) & 0xffff
            ack_checksum = struct.pack('!H', ack_sum)
            ack_packet = ack_bytes + ack_checksum
            if loss_rate > 0 and random.random() < loss_rate:
                print(f"[클라이언트] DupACK#{ack_num} 손실시뮬레이션: 전송 생략")
            else:
                sock.sendto(ack_packet, (SERVER_IP, SERVER_PORT))
                print(f"[클라이언트] DupACK#{ack_num} 전송")

    end_time = time.time()
    elapsed = end_time - start_time
    if bytes_received >= file_size:
        print(f"[클라이언트] 파일 수신 완료! 받은 바이트: {bytes_received}, 시간: {elapsed:.3f}s")
    else:
        print(f"[클라이언트] 파일을 모두 받지 못함. 받은 바이트: {bytes_received}")

    file.close()
    sock.close()

# 클라이언트 실행 예시
if __name__ == "__main__":
    go_back_n_client("1.png", loss_rate=0.0)
