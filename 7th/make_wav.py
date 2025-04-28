import math
import struct
import wave
import reedsolo
import random

INTMAX = 2**(32-1)-1
channels = 1
unit = 0.1
samplerate = 48000


rules = {
'0':768,
'1':896,
'2':1024,
'3':1152,
'4':1280,
'5':1408,
'6':1536,
'7':1664,
'8':1792,
'9':1920,
'A':2048,
'B':2176,
'C':2304,
'D':2432,
'E':2560,
'F':2688}

def make_audio(text):
    uni_data = text.encode('utf-8')
    # RS 인코딩
    rsc = reedsolo.RSCodec(8)
    encoded_bytes = rsc.encode(uni_data)
    encoded_hex = encoded_bytes.hex().upper()
    print(f'RS 인코딩된 16진수: {encoded_hex}')
    hex_length = len(encoded_hex)
    print(f'RS 인코딩된 16진수의 길이: {hex_length}')
    # 오디오 신호 생성
    audio = []
    for s in encoded_hex:
        for i in range(int(unit*samplerate)):
            audio.append(int(INTMAX*math.sin(2*math.pi*rules[s]*i/samplerate)))
    audio2wav(audio, "normal.wav")
    
    # make error
    
    #error_count = random.randint(0, bytes_length/2) # 오류 개수, reedsolo에서는 n/2개의 오류를 복구할 수 있음
    error_count = random.randint(0, 8)
    print(f"주입할 오류 개수 (byte단위 오류): {error_count}")
    
    encoded_bytes_with_errors = bytearray(encoded_bytes)
    indices = random.sample(range(len(encoded_bytes_with_errors)), error_count)

    for idx in indices:
        original_byte = encoded_bytes_with_errors[idx]
        new_byte = random.randint(0, 255)
        while new_byte == original_byte:
            new_byte = random.randint(0, 255)
        encoded_bytes_with_errors[idx] = new_byte
    error_hex = encoded_bytes_with_errors.hex().upper()
    print(f"오류가 주입된 RS 데이터 16진수: {error_hex}")
    
    audio = []
    for s in error_hex:
        for i in range(int(unit*samplerate)):
            audio.append(int(INTMAX*math.sin(2*math.pi*rules[s]*i/samplerate)))
    
    audio2wav(audio, "error.wav")

def audio2wav(audio,filename):
    with wave.open(filename, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(4)
        w.setframerate(48000)
        for a in audio:
            w.writeframes(struct.pack('<l', a))
    print(f"{filename} 파일이 생성되었습니다.\n")