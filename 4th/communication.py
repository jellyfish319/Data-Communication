import math
import statistics
import struct
import time
import wave
import morse_converter as morse

import pyaudio

INITMAX = 32767

def send_data(text):
    audio = morse.morse2audio(morse.text2morse(text))
    
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate = 48000,
                    output= True)

    chunk_size = 1024

    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i+chunk_size]
        stream.write(struct.pack('<'+('h'*len(chunk)),*chunk))

    stream.stop_stream()
    stream.close()
    p.terminate()

def audio2morse():
    m = ''
    p = pyaudio.PyAudio()
    threshold = 220
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = 48000,
                    input = True
                    )

    unit_samples = int(0.1 * 48000)

    # 목표 2
    while True:
        data = stream.read(unit_samples,exception_on_overflow=False)
        samples = struct.unpack('<' + ('h' * unit_samples), data)
        if statistics.mean([abs(s) for s in samples]) > threshold:
            m += '.'
            print(m)
            break

    seen = 0
    while True:
        data = stream.read(unit_samples, exception_on_overflow=False)
        samples = struct.unpack('<' + ('h' * unit_samples), data)
        mean = statistics.mean([abs(s) for s in samples])
        # 목표 1
        if mean > threshold:
            m += '.'
            seen = 0
        else:
            m += ' '
            seen += 1

        print("Signal: ", m)

        # 목표 3
        if seen >= 35:
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Input Signal: " + m)

    m = m.replace('...', '-')
    return m

def receive_data():
    return morse.morse2text(morse.tab2slash(morse.unit2text(audio2morse())))

def main():
    while True:
        print("Morse Code over Sound with Noise")
        print("2025 Spring Data Communication at CNU")
        print('[1] Receive morse code over sound (play)')
        print('[2] Receive morse code over sound (record)')
        print('[q] Exit')
        select=input('Select menu: ').strip().upper()
        if select == '1':
            input_string = input("Type some text to send: ")
            send_data(input_string)
        elif select == '2':
            print("Ready to receive...")
            print(receive_data())
        elif select == 'Q':
            print('Terminating...')
            break
if __name__ =='__main__':
    main()