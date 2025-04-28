import reedsolo
import random
import struct
import wave
import scipy.fftpack
import numpy as np


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
inverse_rules = {v: k for k, v in rules.items()}

def converter(freq):
    for key, value in rules.items():
        if freq >= value-10 and freq <= value+10:
                return key

def restore_error_wav(normal_wav, error_wav):
    # 정상 wav 파일
    with wave.open(normal_wav, 'rb') as w:
        frames = w.readframes(w.getnframes())
        normal_audio = np.array(struct.unpack('<' + 'i' * (len(frames)//4), frames), dtype=np.int32)
    
    # 오류 wav 파일
    with wave.open(error_wav, 'rb') as w:
        frames = w.readframes(w.getnframes())
        error_audio = np.array(struct.unpack('<' + 'i' * (len(frames)//4), frames), dtype=np.int32)
        
    # 원본의 주파수 분석
    samples_per_symbol = int(unit * samplerate)
    num_symbols = len(normal_audio) // samples_per_symbol

    normal_hex_string = ""
    for i in range(num_symbols):
        samples = normal_audio[i*samples_per_symbol:(i+1)*samples_per_symbol]

        freq = scipy.fftpack.fftfreq(len(samples), d=1/samplerate)
        fourier = scipy.fftpack.fft(samples)
        freq_max = freq[np.argmax(abs(fourier))]

        hex_char = converter(freq_max)
        normal_hex_string += hex_char
    
    # 오류의 주파수 분석
    error_sybol = len(error_audio) // samples_per_symbol
    error_hex_string = ""
    for i in range(error_sybol):
        samples = error_audio[i*samples_per_symbol:(i+1)*samples_per_symbol]

        freq = scipy.fftpack.fftfreq(len(samples), d=1/samplerate)
        fourier = scipy.fftpack.fft(samples)
        freq_max = freq[np.argmax(abs(fourier))]

        hex_char = converter(freq_max)
        error_hex_string += hex_char

    # 바이트 단위 오류 개수 탐지
    normal_bytes = bytes.fromhex(normal_hex_string)
    error_bytes = bytes.fromhex(error_hex_string)

    error_count = 0
    min_len = min(len(normal_bytes), len(error_bytes))
    for i in range(min_len):
        if normal_bytes[i] != error_bytes[i]:
            error_count += 1

    print(f"오류 개수(byte): {error_count}")
    
    # RS 디코딩
    try:
        encoded_bytes_with_errors = bytes.fromhex(error_hex_string)
        rsc = reedsolo.RSCodec(8)
        decoded_bytes = rsc.decode(encoded_bytes_with_errors)[0]
        recovered_text = decoded_bytes.decode('utf-8')
        print("\nRS 디코딩 성공!")
        print("복원된 메시지:")
        print(recovered_text)
    except reedsolo.ReedSolomonError as e:
        print("\nRS 디코딩 실패!")
        print(e)
    except UnicodeDecodeError as e:
        print("\nRS 디코딩은 되었으나, UTF-8 디코딩에 실패했습니다.")
        print(e)