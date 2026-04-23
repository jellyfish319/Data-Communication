import socket
import random
FLAGS = _ = None
DEBUG = False

def main():
    if DEBUG:
        print(f'Parsed arguments {FLAGS}')
        print(f'Unparsed arguments {_}')
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((FLAGS.address,FLAGS.port))
    
    print(f'Listening on {sock}')
    while True:
        bag = []
        for i in range(1, 46):
            bag.append(i)
        data,client=sock.recvfrom(2**16)
        data=data.decode('utf-8')
        data = data.strip()
        print(f'Received {data} from {client}')
        print(f'Numbers in bag: {bag}')

        if data:  # 데이터가 비어있지 않을 때만 처리
            dataNum = data.split(' ')
            length = len(dataNum)
            if DEBUG:
                print(f'Numbers in data: {dataNum}')
                print(f'Length of data: {length}')
            for i in range(length):
                bag.remove(int(dataNum[i]))
            output = random.sample(bag, 6-length)
        else:  # 데이터가 비어있으면 6개 전부 랜덤 선택
            length = 0
            output = random.sample(bag, 6)
        
        dataNum = list(map(int, data.split(' '))) if data else []
        final = dataNum + output
        final = sorted(final)
        
        final_str = ' '.join(map(str, final))
        sock.sendto(final_str.encode('utf-8'), client)
        print(f'Send {final} to {client}')
        
if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--debug',action='store_true',
    help='The present debug message')
    parser.add_argument('--address',type=str,default='127.0.0.1',
    help='The address to serve service')
    parser.add_argument('--port',type=int,default=3034,
    help='The port to serve service')
    FLAGS,_=parser.parse_known_args()
    DEBUG=FLAGS.debug
    main()