import time

# 수신자 #1 전용
DATAFILE_R1 = "data_r1"
SIGNALFILE_R1 = "signal_r1"

# 수신자 #2 전용
DATAFILE_R2 = "data_r2"
SIGNALFILE_R2 = "signal_r2"

# 1) 보낼 문자열 입력
input_string = input("Input string to send: ")

# 2) 입력 문자열을 8비트 이진수로 변환
bit_msg = ''.join([bin(ord(ch))[2:].zfill(8) for ch in input_string])
print("Sender started.\n")

n = 8
splitData_sender = [bit_msg[i:i+n] for i in range(0, len(bit_msg), n)]
print("[Sender] Data to send (8-bit chunks):", splitData_sender)

# 송신자 문자 확인용
reconstructed = ""
for bits_chunk in splitData_sender:
    if len(bits_chunk) == 8:
        reconstructed += chr(int(bits_chunk, 2))

print("[Sender] (Check) Reconstructed from bit_msg:", reconstructed)
print()

i = 0
while i < len(bit_msg):
    bit_to_send = bit_msg[i]

    #
    # --- (1) 수신자 #1에게 전송 ---
    #
    # (1-1) 수신자 #1이 signal="1"(준비 완료)될 때까지 대기
    ready_r1 = False
    while not ready_r1:
        with open(SIGNALFILE_R1, "r") as f:
            status_r1 = f.read().strip()
        if status_r1 == "1":
            ready_r1 = True
        else:
            time.sleep(0.01)

    # (1-2) data_r1에 현재 비트 쓰고, signal_r1="0"
    with open(DATAFILE_R1, "w") as f:
        f.write(bit_to_send)
    print(f"[Sender] Wrote bit '{bit_to_send}' to R1")

    with open(SIGNALFILE_R1, "w") as f:
        f.write("0")

    # (1-3) 수신자 #1이 읽고 signal_r1="1"로 돌아올 때까지 대기
    done_r1 = False
    while not done_r1:
        with open(SIGNALFILE_R1, "r") as f:
            status_r1 = f.read().strip()
        if status_r1 == "1":
            done_r1 = True
        else:
            time.sleep(0.01)

    #
    # --- (2) 수신자 #2에게 전송 ---
    #
    
    ready_r2 = False
    while not ready_r2:
        with open(SIGNALFILE_R2, "r") as f:
            status_r2 = f.read().strip()
        if status_r2 == "1":
            ready_r2 = True
        else:
            time.sleep(0.01)

    with open(DATAFILE_R2, "w") as f:
        f.write(bit_to_send)
    print(f"[Sender] Wrote bit '{bit_to_send}' to R2")

    with open(SIGNALFILE_R2, "w") as f:
        f.write("0")

    done_r2 = False
    while not done_r2:
        with open(SIGNALFILE_R2, "r") as f:
            status_r2 = f.read().strip()
        if status_r2 == "1":
            done_r2 = True
        else:
            time.sleep(0.01)
    
    i += 1

# 모든 비트 전송 완료 -> signal="2"로 종료 알림
with open(SIGNALFILE_R1, "w") as f:
    f.write("2")
with open(SIGNALFILE_R2, "w") as f:
    f.write("2")

print("\n[Sender] All bits sent! Transmission done.")
