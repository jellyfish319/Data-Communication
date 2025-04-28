import math
import struct
import wave
import pyaudio

INTMAX = 2**(16-1)-1
channels = 1
unit = 0.1
samplerate = 48000

FREQ_START = 512
FREQ_STEP = 128
HEX_LIST=['0','1','2','3','4',
'5','6','7','8','9',
'A','B','C','D','E',
'F']
HEX=set(HEX_LIST)

rules = {}
rules['START'] = FREQ_START
for i in range(len(HEX_LIST)):
    h = HEX_LIST[i]
    rules[h] = FREQ_START + FREQ_STEP + FREQ_STEP*(i+1)
rules['END'] = FREQ_START + FREQ_STEP + FREQ_STEP*(len(HEX_LIST)) + FREQ_STEP*2

def sender(text):
    string_hex=text.encode('utf-8').hex().upper()
    print(f'Unicode: {string_hex}')
    
    audio = []
    for i in range(int(unit*samplerate*2)):
        audio.append(int(INTMAX*math.sin(2*math.pi*rules['START']*i/samplerate)))
    for s in string_hex:
        for i in range(int(unit*samplerate*1)):
            audio.append(int(INTMAX*math.sin(2*math.pi*rules[s]*i/samplerate)))
    for i in range(int(unit*samplerate*2)):
        audio.append(int(INTMAX*math.sin(2*math.pi*rules['END']*i/samplerate)))
    
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=samplerate,
                    output=True)
    
    chunk_size = 1024
    for i in range(0,len(audio), chunk_size):
        chunk = audio[i:i+chunk_size]
        stream.write(struct.pack('<'+('h'*len(chunk)), *chunk))