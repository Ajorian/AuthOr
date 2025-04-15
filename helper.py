import struct
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

TAGS_LENGTH_BYTES = 16
iv = os.urandom(TAGS_LENGTH_BYTES)
key = os.urandom(TAGS_LENGTH_BYTES)

RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'  # Reset to default color
BLUE = '\033[34m'

def XOR(v1, v2):
    x = bytes(x ^ y for x, y in zip(v1, v2))
    return x

def hash(i:str,bytes):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(bytes) + encryptor.finalize()
    ii = i.encode().ljust(16, b'\x00') # valid implementation must be XOR((ii||bytes), Enc(bytes||ii)) which generates 256 bytes then i must break it into two parts and xor them
    if len(ii)!= len(ct) or len(bytes)!= len(ct):
        raise Exception('mismatch data length in hash function for ' + repr(bytes))
    
    return XOR(ii,XOR(ct,bytes))

def randtag():
    tag = secrets.token_bytes(TAGS_LENGTH_BYTES)
    return tag

def tagtostr(bytes):
    return bytes.hex()[:5]

delta = randtag()

def custom_sort_key(s):
    if s[-1].isdigit(): # Check if the string ends with a digit
        return (1, int(''.join(filter(str.isdigit, s))))  # Return a tuple (1, number)
    else: return (0, s)  # Return a tuple (0, string) for non-numeric

def estimate_distribution(values):
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    return (mean,std_dev)

def float64_to_binary(num):
    packed = struct.pack('!d', num)  # '!d' for big-endian double
    return ''.join(f'{b:08b}' for b in packed)

def hex_to_float64(val):
    integer_value = int(val, 16)
    packed = struct.pack('!Q', integer_value)  # '!Q' for big-endian unsigned long long
    return struct.unpack('!d', packed)[0]  # Unpack as double

def hex_to_ascii(hex_string):
    if hex_string.startswith('0x'):
        hex_string = hex_string[2:]
    ascii_string = ''.join(chr(int(hex_string[i:i+2], 16)) for i in range(0, len(hex_string), 2))
    return ascii_string