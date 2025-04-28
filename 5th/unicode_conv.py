def str2uni(text):
    # str=>hex
    byte_hex = text.encode('utf-8')
    byte_string = byte_hex.hex().upper()
    print(f'Byte String: {byte_string}')
    return byte_string

def uni2str(byte_string):
    # byte_string => str
    client_byte_hex = bytes.fromhex(byte_string)
    client_byte_string = client_byte_hex.hex().upper()
    print(f'Client Byte String: {client_byte_string}')
    client_output = client_byte_hex.decode('utf-8')
    return client_output
