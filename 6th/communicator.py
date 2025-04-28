import sender as send
import receiver as recv
import math
import statistics
import struct
import time
import wave
import pyaudio

def send_data():
    input_text = input("Type some text to send: ")
    send.sender(input_text)

def receive_data():
    recv.receive()

def main():
    while True:
        print('Unicode over Sound with Noise')
        print('2025 Spring Data Communication at CNU')
        print('[1] Send Unicode over Sound(play)')
        print('[2] Receive Unicode over Sound(record)')
        print('[q] Exit')
        select = input('Select menu:').strip().upper()
        if select == '1':
            send_data()
        elif select == '2':
            print("Ready to receive")
            receive_data()
        elif select == 'Q':
            print('Terminating...')
            break

if __name__ =='__main__':
    main()