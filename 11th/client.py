import socket
FLAGS = _ = None
DEBUG = False
def main():
    if DEBUG:
        print(f'Parsed arguments {FLAGS}')
        print(f'Unparsed arguments {_}')
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    print(f'Ready to send using {sock}')
    while True:
        data = input('Data: ').strip()
        sock.sendto(data.encode('utf-8'),(FLAGS.address,FLAGS.port))
        print(f'Send {data} to ({FLAGS.address},{FLAGS.port})')
        data, server = sock.recvfrom(2**16)
        data = data.decode('utf-8')
        print(f'Received {data} from {server}')

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