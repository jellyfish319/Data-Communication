import socket
import struct
import time
import math
import random

# 서버 설정 (VM 내 IP와 포트)
SERVER_IP = '0.0.0.0'
SERVER_PORT = 3034

# Go-Back-N ARQ 서버
def go_back_n_server(filename, window_size=15, loss_rate=0.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    print(f"[서버] Go-Back-N ARQ 서버 시작 (윈도우 크기={window_size}, 손실률={loss_rate*100:.1f}%)")

    # 파일 읽기
    try:
        with open(filename, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"[서버] 파일을 찾을 수 없습니다: {filename}")
        return

    file_size = len(file_data)
    print(f"[서버] 전송할 파일 크기: {file_size} 바이트")

    # INFO 요청 처리
    data, client_addr = sock.recvfrom(2048)
    request = data.decode('utf-8', errors='ignore')
    if request.startswith("INFO"):
        if file_size > 0:
            response = str(file_size).encode('utf-8')
        else:
            response = "404 Not Found".encode('utf-8')
        sock.sendto(response, client_addr)
        print("[서버] 파일 크기 정보 응답 완료.")

    # DOWNLOAD 요청 처리
    data, client_addr = sock.recvfrom(2048)
    request = data.decode('utf-8', errors='ignore')
    if not request.startswith("DOWNLOAD"):
        print("[서버] DOWNLOAD 요청을 받지 못했습니다. 종료합니다.")
        return
    print("[서버] 파일 데이터 전송 시작...")

    # 파일 데이터를 패킷 단위로 준비
    # 미리 1456바이트씩 잘라 리스트로 보관 (필요 시 on-the-fly로 생성 가능)
    chunks = [file_data[i:i+1456] for i in range(0, file_size, 1456)]
    total_packets = len(chunks)
    print(f"[서버] 총 패킷 수: {total_packets}")

    base_index = 0        # 윈도우 내 첫 번째(보내졌지만 ACK 안 된) 패킷의 절대 인덱스
    next_index = 0        # 보내지지 않은 다음 패킷의 절대 인덱스
    seq_base = 0          # base_index의 시퀀스 번호 (base_index mod 16)
    seq_next = 0          # next_index의 시퀀스 번호 (next_index mod 16)
    bytes_sent = 0
    start_time = time.time()
    sock.settimeout(0.1)  # 수신 대기는 폴링 방식 (0.1초마다 깨어남)

    # 보낼 데이터가 남아있거나 ACK 대기 중인 것이 있으면 루프 지속
    while base_index < total_packets:
        # 윈도우 범위 내에서 가능한 만큼 새로운 패킷 전송
        while next_index < total_packets and (next_index - base_index) < window_size:
            # 패킷 생성
            seq_num = next_index % 16
            chunk = chunks[next_index]
            # 헤더 생성
            seq_bytes = struct.pack('!H', seq_num)
            temp_packet = seq_bytes + b'\x00\x00' + chunk
            checksum_val = 0
            for i in range(0, len(temp_packet), 2):
                two_bytes = temp_packet[i:i+2]
                if len(two_bytes) < 2:
                    two_bytes += b'\x00'
                checksum_val += struct.unpack('!H', two_bytes)[0]
                checksum_val &= 0xffff
            checksum_val = (~checksum_val) & 0xffff
            checksum_bytes = struct.pack('!H', checksum_val)
            packet = seq_bytes + checksum_bytes + chunk

            # 패킷 전송 (loss_rate에 따라 전송 스킵 가능)
            if loss_rate > 0 and random.random() < loss_rate:
                print(f"[서버] 패킷 #{seq_num} 전송 **손실시뮬레이션: 전송 생략**")
            else:
                sock.sendto(packet, client_addr)
                print(f"[서버] >> #{seq_num} (Index:{next_index}) 패킷 전송 [{len(chunk)} bytes]")
            next_index += 1
            # 타이머는 아래에서 ACK 대기 처리하면서 관리

        # ACK 수신 대기 (non-blocking 폴링 with timeout)
        try:
            ack_packet, _ = sock.recvfrom(1024)
        except socket.timeout:
            # 타임아웃 발생: ACK가 전혀 도착하지 않은 경우
            # 현재 윈도우의 base_index 패킷부터 다시 전송
            # (Go-Back-N: base부터 next_index-1까지 재전송)
            if base_index < next_index:
                print(f"[서버] *** ACK 타임아웃 발생! 패킷 #{base_index % 16} (Index:{base_index})부터 재전송 ***")
            for idx in range(base_index, next_index):
                seq_num = idx % 16
                chunk = chunks[idx]
                seq_bytes = struct.pack('!H', seq_num)
                # 체크섬은 이전에 계산된 것을 재활용할 수도 있지만 여기 간단히 다시 계산
                temp_packet = seq_bytes + b'\x00\x00' + chunk
                checksum_val = 0
                for i in range(0, len(temp_packet), 2):
                    two_bytes = temp_packet[i:i+2]
                    if len(two_bytes) < 2:
                        two_bytes += b'\x00'
                    checksum_val += struct.unpack('!H', two_bytes)[0]
                    checksum_val &= 0xffff
                checksum_val = (~checksum_val) & 0xffff
                checksum_bytes = struct.pack('!H', checksum_val)
                packet = seq_bytes + checksum_bytes + chunk

                # 손실 시뮬레이션 적용
                if loss_rate > 0 and random.random() < loss_rate:
                    print(f"[서버] (재전송) 패킷 #{seq_num} 손실시뮬레이션: 전송 생략")
                else:
                    sock.sendto(packet, client_addr)
                    print(f"[서버] 재전송 >> #{seq_num} (Index:{idx}) 패킷 전송")
            # 재전송 후 계속 ACK 대기 루프 진행
            continue

        # ACK 패킷을 받았을 경우 처리:
        if len(ack_packet) >= 4:
            ack_seq = struct.unpack('!H', ack_packet[:2])[0]
            recv_checksum = struct.unpack('!H', ack_packet[2:4])[0]
        else:
            # 잘못된 패킷이면 무시
            continue

        # ACK 체크섬 검증
        calc = (ack_seq + 0) & 0xffff
        calc = (~calc) & 0xffff
        if calc != recv_checksum:
            print("[서버] ACK 체크섬 오류 - ACK 무시")
            continue

        # 유효한 ACK인 경우
        ack_num = ack_seq  # 클라이언트가 기대하는 다음 패킷 번호 (0~15)
        # ack_num는 base_index의 seq + acked_count (mod 16) 형태일 것
        # base_index와 ack_seq 비교하여 몇 개가 ACK됐는지 계산
        base_seq = base_index % 16
        # 누적 ACK 개수 계산
        acked_count = 0
        if ack_num >= base_seq:
            acked_count = ack_num - base_seq
        else:
            acked_count = (16 - base_seq) + ack_num
        if acked_count == 0:
            # 중복 ACK (이미 처리한 ACK을 다시 받았거나, 아직 새로운 ACK가 없을 때)
            print(f"[서버] 중복 ACK#{ack_num} 수신 - 무시")
            continue

        # 윈도우 이동: base_index를 ACKed count만큼 증가
        new_base = base_index + acked_count
        # acked_count가 현재 윈도우 크기보다 큰 경우는 없음 (Go-Back-N에서는 순차 ACK)
        base_index = new_base
        print(f"[서버] ACK#{ack_num} 수신 - base_index가 {base_index}로 이동")
        bytes_sent = base_index * 1456 if base_index < total_packets else file_size  # 전송된 바이트 (마지막은 남은 바이트)
        # 만약 모든 패킷이 ACK되었다면 루프 종료
        if base_index >= total_packets:
            break
        # base_index가 변했으니 타이머 리셋 효과 (socket.timeout이 0.1로 계속 돎)
        # -> 구현상 특별히 리셋 로직 없이 timeout 계속 발생시 재전송하도록 위에서 처리
        # Go-Back-N에서는 별도 타이머 관리 필요하지만 여기선 단순화를 위해 모든 패킷 동일 timeout으로 취급

    # 모든 데이터 전송 완료, 마지막 ACK 수신 후 종료
    end_time = time.time()
    elapsed = end_time - start_time
    throughput = (bytes_sent * 8) / elapsed if elapsed > 0 else 0.0
    print(f"[서버] 파일 전송 완료! 총 전송 바이트: {bytes_sent}, 걸린 시간: {elapsed:.3f}s, Throughput: {throughput:.2f} bps")

    sock.close()

# 서버 실행 예시
if __name__ == "__main__":
    go_back_n_server("1.png", window_size=15, loss_rate=0.0)
