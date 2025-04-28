import time

DATAFILE = "data_r2"
SIGNALFILE = "signal_r2"

data_bits = ""
print("[Receiver #2] Waiting for data...")

# 이곳의 빈공간을 채워주세요

with open(SIGNALFILE, "w") as f:
    f.write("1")

while True:
    time.sleep(0.01)

    with open(SIGNALFILE, "r") as f:
        status = f.read().strip()

    if status == "2":
        print("[Receiver #2] Got signal 2. Stop receiving.")
        break

    if status == "0":
        with open(DATAFILE, "r") as f:
            bit = f.read().strip()

        data_bits += bit
        print(f"[Receiver #2] Read bit: {bit}")

        # 읽었으니, signal=1로 돌림
        with open(SIGNALFILE, "w") as f:
            f.write("1")

# split 부분
characters = ""
n = 8
splitData = [data_bits[i:i+n] for i in range(0, len(data_bits), n)]
print("[Receiver #2] Data received:", str(splitData))

i = 0
for _ in splitData:
    splitString = splitData[i]
    splitInteger = int(splitString, 2)
    characters += chr(splitInteger)
    i += 1

print("[Receiver #2] Message Converted:", characters)