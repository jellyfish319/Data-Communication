import random
import reedsolo

RSC_LEN=4
HEX={'0','1','2','3','4',
'5','6','7','8','9',
'A','B','C','D','E',
'F'}
text=' 사용자입력! '
byte_hex=text.encode('utf-8')
string_hex=byte_hex.hex().upper()
rsc=reedsolo.RSCodec(RSC_LEN)
byte_rsc=rsc.encode(byte_hex)
string_rsc=byte_rsc.hex().upper()
print(f'인코딩:{string_rsc}')
client_string_rsc=string_rsc
client_byte_hex=bytes.fromhex(client_string_rsc)
client_rsc=reedsolo.RSCodec(RSC_LEN)
client_byte=client_rsc.decode(client_byte_hex)[0]
client_text=client_byte.decode('utf-8')
print(f'디코딩:{client_text}')

client_rsc = reedsolo.RSCodec(RSC_LEN)

for i in range(0, RSC_LEN):
    client_string_rsc = string_rsc
    client_string_list = list(client_string_rsc)
    
    for r in random.sample(range(0, len(client_string_list) // 2), k=i):
        m = random.randint(0, 2)
        if m == 0:
            client_string_list[(r - 1) * 2] = random.choice(list(HEX - {client_string_list[(r - 1) * 2]}))
        elif m == 1:
            client_string_list[(r - 1) * 2 + 1] = random.choice(list(HEX - {client_string_list[(r - 1) * 2 + 1]}))
        elif m == 2:
            client_string_list[(r - 1) * 2] = random.choice(list(HEX - {client_string_list[(r - 1) * 2]}))
            client_string_list[(r - 1) * 2 + 1] = random.choice(list(HEX - {client_string_list[(r - 1) * 2 + 1]}))
    
    client_string_rsc = ''.join(client_string_list)
    client_byte_hex = bytes.fromhex(client_string_rsc)
    
    try:
        client_byte = client_rsc.decode(client_byte_hex)[0]
        client_text = client_byte.decode('utf-8')
        if client_text == text:
            print(f'{i}개 오류 통과:')
            print(f'> {string_rsc}')
            print(f'> {client_string_rsc}')
    except reedsolo.ReedSolomonError:
        print(f'{i}개 오류 통과 실패:')
        print(f'> {string_rsc}')
        print(f'> {client_string_rsc}')
        break