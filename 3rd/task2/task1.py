import sys
import math
import wave
import struct
import statistics

INTMAX = 2**(32-1)-1
t = 1.0
fs = 48000
f = 261.626 # C4, 도를 나타냄
audio = []
for i in range(int(t*fs)):
    audio.append(int(INTMAX*math.sin(2*math.pi*f*(i/fs))))

filename = 't.wav'
with wave.open(filename, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(4)
    w.setframerate(48000)
    for a in audio:
        w.writeframes(struct.pack('<l',a))

