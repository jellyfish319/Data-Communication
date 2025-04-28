import sys
import math
import wave
import struct
import statistics
import argparse

english={'A':'.-','B':'-...','C':'-.-.',
'D':'-..','E':'.','F':'..-.',
'G':'--.','H':'....','I':'..',
'J':'.---','K':'-.-','L':'.-..',
'M':'--','N':'-.','O':'---',
'P':'.--.','Q':'--.-','R':'.-.',
'S':'...','T':'-','U':'..-',
'V':'...-','W':'.--','X':'-..-',
'Y':'-.--','Z':'--..'}

number={'1':'.----','2':'..---','3':'...--',
'4':'....-','5':'.....','6':'-....',
'7':'--...','8':'---..','9':'----.',
'0':'-----'}

def text2morse(text):
    text = text.upper()
    morse = ''
    
    for t in text:
        if t == ' ':
            morse = morse + '/ ' 
        for key, value in english.items():
            if t == key:
                morse = morse + value + " "
        for key, value in number.items():
            if t == key:
                morse = morse + value + " "
    return morse

def morse2audio(morse):
    INTMAX = 2**(32-1)-1
    t = 0.1
    fs = 48000
    f = 523.251
    audio = []
    for m in morse:
        if m == '.':
            for i in range(int(t*fs*1)):
                audio.append(int(INTMAX*math.sin(2*math.pi*f*(i/fs))))
            for i in range(int(t*fs*1)):
                audio.append(int(0))
        elif m == '-':
            for i in range(int(t*fs*3)):
                audio.append(int(INTMAX*math.sin(2*math.pi*f*(i/fs))))
            for i in range(int(t*fs*1)):
                audio.append(int(0)) # dot와 dash 사이의 1unit 추가
        elif m == '/':
            for i in range(int(t*fs*2)):
                audio.append(int(0)) # 단어와 단어 사이 공백, 문자와 문자 사이는 무조건 dash 혹은 dot로 끝나므로 dot의 끝인 1unit+ 1공백 신호가 추가된 상태임 또한, 마지막에도 1공백신호가 추가되므로 2공백신호 + 1unit인 5unit이 이미 할당되어 있는 상황, 따라서 2unit을 추가
        elif m == ' ':
            for i in range(int(t*fs*2)):
                audio.append(int(0)) # 문자와 문자 사이, 문자와 문자 사이는 무조건 dash 혹은 dot로 끝나므로 1unit 공백 신호가 추가된 상태임 따라서 2unit을 추가

    return audio

def audio2file(audio,filename):
    with wave.open(filename, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(4)
        w.setframerate(48000)
        for a in audio:
            w.writeframes(struct.pack('<l', a))

def file2morse(filename):
    with wave.open(filename, 'rb') as w:
        audio = []
        framrate = w.getframerate()
        frames = w.getnframes()
        for i in range(frames):
            frame = w.readframes(1)
            audio.append(struct.unpack('<i',frame)[0])
        morse = ''
        unit = int(0.1*48000)
        for i in range(1,math.ceil(len(audio)/unit)+1):
            stdev = statistics.stdev(audio[(i-1)*unit:i*unit])
            if stdev > 10000:
                morse = morse + '.'
            else:
                morse = morse + ' '
        morse = morse.replace('...','-')
    return morse

def unit2text(input):
    output = ""
    for i in range(0,len(input),2):
        if input[i] == ".":
            output = output + "."
        elif input[i] == "-":
            output = output + "-"
        elif input[i] == " ":
            output = output + " "
    return output

def tab2slash(input):
    input_list = list(input)
    for i in range(0, len(input_list)-1):
        if input_list[i] == " " and input_list[i+1] == " ":
            input_list[i+1] = "/"
    return "".join(input_list)

def convert(word):
    for key, val in english.items():
        if val == word:
            return key
    for key, val in number.items():
        if val == word:
            return key

def morse2text(morse):
    letter = ""
    text = ""
    
    for t in morse:
        if t != " ":
            if t == "/": 
                text = text + " "
            else:
                letter = letter + t
        else:
            if letter:
                text = text + convert(letter)
                letter = ""
    
    if letter:
        text = text + convert(letter)
    
    return text
        
def main():
    parser = argparse.ArgumentParser(description="Converter for Morse Code")
    parser.add_argument("function", choices=["encoding", "decoding"], help="Choose function to use for morse code / encoding or decoding")

    args = parser.parse_args()

    if args.function == "encoding":
        input_string = input("Input string to encode: ")
        morse = text2morse(input_string) 
        print(morse + "\n")
        audio2file(morse2audio(morse), input_string+".wav")
        print("Complete to convert")

    elif args.function == "decoding":
        input_string_file = input("Input wav file name to decode: ")
        print("Original Unit: " + file2morse(input_string_file) + "\n")
        print("Converted Unit: " + unit2text(file2morse(input_string_file))+ "\n")
        print("Morse Code: " + tab2slash(unit2text(file2morse(input_string_file)))+ "\n")
        print("Text: " + morse2text(tab2slash(unit2text(file2morse(input_string_file)))))

if __name__ == "__main__":
    main()
