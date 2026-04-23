# UDP Lotto Client – 숫자 최대 6개 전송 후 결과 수신
# 사용 예:  python udp_lotto_client.py --address 127.0.0.1 --port 3035

import socket
import argparse
from typing import List

NUM_MIN, NUM_MAX = 1, 45
LOTTO_CNT = 6

def prompt_numbers() -> List[int]:
    raw = input("1~45 숫자 0~6개 입력(공백 구분, 엔터=없음): ").strip()
    if not raw:
        return []

    try:
        nums = [int(x) for x in raw.split()]
    except ValueError:
        raise ValueError("모든 값은 정수여야 합니다.")
    if not (0 <= len(nums) <= LOTTO_CNT):
        raise ValueError("숫자는 0~6개까지만 입력해야 합니다.")
    if any(n < NUM_MIN or n > NUM_MAX for n in nums):
        raise ValueError("모든 숫자는 1~45 사이여야 합니다.")
    if len(set(nums)) != len(nums):
        raise ValueError("중복된 숫자가 있으면 안 됩니다.")
    return nums

def run(server_ip: str, server_port: int, timeout: float = 3.0) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    try:
        nums = prompt_numbers()
    except Exception as exc:
        print("입력 오류:", exc)
        return

    payload = " ".join(map(str, nums))
    sock.sendto(payload.encode("utf-8"), (server_ip, server_port))
    print(f"→ Sent: {payload or '(빈 전송)'}")

    try:
        data, _ = sock.recvfrom(1024)
        print("← Reply:", data.decode("utf-8"))
    except socket.timeout:
        print("서버 응답 대기 시간 초과!")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="UDP Lotto Number Client")
    ap.add_argument("--address", required=True, help="서버 IP")
    ap.add_argument("--port",    type=int, required=True, help="서버 포트")
    args = ap.parse_args()
    run(args.address, args.port)
