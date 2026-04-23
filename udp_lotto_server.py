# UDP Lotto Server – 1~45 로또 번호 6개 생성 후 반환
# 사용 예:  python udp_lotto_server.py --address 0.0.0.0 --port 3035

import socket
import random
import argparse
from typing import Set, Tuple, List

# ───── 기본 설정 ──────────────────────────────────────────────────────────
NUM_MIN, NUM_MAX = 1, 45   # 번호 범위
LOTTO_CNT = 6              # 총 개수

# ───── 헬퍼 함수 ──────────────────────────────────────────────────────────
def parse_numbers(payload: str) -> Set[int]:
    """공백 구분 문자열을 Set[int]로 변환하면서 검증."""
    if not payload:
        return set()

    try:
        nums = [int(x) for x in payload.split()]
    except ValueError:
        raise ValueError("모든 값은 정수여야 합니다.")

    if not (0 <= len(nums) <= LOTTO_CNT):
        raise ValueError("숫자는 0~6개까지만 보낼 수 있습니다.")
    if any(n < NUM_MIN or n > NUM_MAX for n in nums):
        raise ValueError("숫자는 1~45 범위여야 합니다.")
    if len(set(nums)) != len(nums):
        raise ValueError("중복된 숫자가 있으면 안 됩니다.")
    return set(nums)

def complete_lotto(basis: Set[int]) -> List[int]:
    """basis 숫자를 포함해 6개가 되도록 무작위로 채워 반환(오름차순)."""
    available = set(range(NUM_MIN, NUM_MAX + 1)) - basis
    needed = LOTTO_CNT - len(basis)
    extra = random.sample(sorted(available), needed) if needed else []
    return sorted(basis | set(extra))

# ───── 메인 루프 ──────────────────────────────────────────────────────────
def serve(bind_addr: str, bind_port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_addr, bind_port))
    print(f"[+] UDP Lotto server listening on {bind_addr}:{bind_port}")

    while True:
        data, client = sock.recvfrom(1024)
        try:
            basis = parse_numbers(data.decode("utf-8").strip())
            numbers = complete_lotto(basis)
            reply = " ".join(map(str, numbers))
        except Exception as exc:
            reply = f"ERROR: {exc}"

        sock.sendto(reply.encode("utf-8"), client)
        print(f"{client}: recv={data.decode('utf-8').strip() or '∅'}  →  send={reply}")

# ───── CLI 엔트리 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="UDP Lotto Number Server")
    ap.add_argument("--address", default="0.0.0.0", help="바인드 IP (기본: 0.0.0.0)")
    ap.add_argument("--port",    type=int, default=3035, help="포트 (기본: 3035)")
    args = ap.parse_args()
    serve(args.address, args.port)
