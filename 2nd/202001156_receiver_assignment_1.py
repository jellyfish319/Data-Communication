import time

DATAFILE = "data_r1"
SIGNALFILE = "signal_r1"

data_bits = ""
print("[Receiver #1] Waiting for data...")

# 초기화: receiver 준비 -> signal=1
with open(SIGNALFILE, "w") as f:
    f.write("1")

while True:
    time.sleep(0.01)

    # signal 읽기
    with open(SIGNALFILE, "r") as f:
        status = f.read().strip()

    # "2" -> 전송 종료
    if status == "2":
        print("[Receiver #1] Got signal 2. Stop receiving.")
        break

    # "0" -> 송신자가 새 비트를 data 파일에 썼음
    if status == "0":
        with open(DATAFILE, "r") as f:
            bit = f.read().strip()

        data_bits += bit
        print(f"[Receiver #1] Read bit: {bit}")

        # 읽었으니, signal=1로 돌림
        with open(SIGNALFILE, "w") as f:
            f.write("1")

# 여기서부터 splitData 방식으로 디코딩
characters = ""
n = 8
splitData = [data_bits[i:i+n] for i in range(0, len(data_bits), n)]
print("[Receiver #1] Data received:", str(splitData))

i = 0
for _ in splitData:
    splitString = splitData[i]
    splitInteger = int(splitString, 2)
    characters += chr(splitInteger)
    i += 1

print("[Receiver #1] Message Converted:", characters)
