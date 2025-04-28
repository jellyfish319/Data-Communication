import wave
import struct

import scipy.fftpack
import numpy as np
import pyaudio
import unicode_conv as uni

unit = 0.1

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


def converter(freq):
    for key, value in rules.items():
        if freq >= value-10 and freq <= value+10:
            if key == 'END' or key == 'START':
                return ''
            else:
                return key

def receive():
    word = ''
    p = pyaudio.PyAudio()
    threshold = 510
    samplerate = 48000
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = 48000,
                    input = True
                    )

    unit_samples = int(0.1 * 48000)

    count = 0

    while True:
        data = stream.read(unit_samples,exception_on_overflow=False)
        samples = struct.unpack('<' + ('h' * unit_samples), data)

        freq = scipy.fftpack.fftfreq(len(samples), d=1/samplerate)
        fourier = scipy.fftpack.fft(samples)
        freq_max = freq[np.argmax(abs(fourier))]

        print(f'[Start]: {freq_max}')
        
        if freq_max == threshold:
            count += 1
            if count == 2:
                break
        else:
            count = 0

    while True:
        data = stream.read(unit_samples, exception_on_overflow=False)
        samples = struct.unpack('<' + ('h' * unit_samples), data)
        freq = scipy.fftpack.fftfreq(len(samples), d=1/samplerate)
        fourier = scipy.fftpack.fft(samples)
        freq_max = freq[np.argmax(abs(fourier))]
        print(f'[Data]: {freq_max}')
        spell = converter(freq_max)
        if spell:
            word += spell

        print(f'Current Data: {word}')

        if freq_max == 2940 or freq_max == 2950:
            count += 1
            print(f'[END]: {freq_max}')
            if count == 2:
                break
        else:
            count = 0
        
    stream.stop_stream()
    stream.close()
    p.terminate()

    text = uni.uni2str(word)
    print(f'Receive Message: {text}')