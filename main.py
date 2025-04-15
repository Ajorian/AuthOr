import time
import os
import random
from hg import HGGarbler
from compiler import ps_compile
from authOr import AuthOrGarbler
from bristol_fassion import bf_compile
from helper import *
import re

def test(benchmark, num_of_trials=10):
    folder = f'circuits/{benchmark}'
    ret =''
    gains = []
    for filename in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, filename)):
            if filename.startswith('__'): continue
            print(f'testing {benchmark}/{filename} ...')
            stats = test_circuit(benchmark,filename,num_of_trials)
            gains.append(stats['ctOVH'])
            ret += to_latex(filename.split('.')[0],stats) + '\n'
    ret += f' & & & & & & & Average: {sum(gains)/len(gains):.3f} \\\ \hline'

    return ret

def to_latex(name,stats):
    ret = f'{name}'
    ret += f' & {stats['gbHGG']:.3f} & {stats['evHGG']:.3f} & {int(stats['ctHGG'])}'
    ret += f' & {stats['gbAOG']:.3f} & {stats['evAOG']:.3f} & {int(stats['ctAOG'])}'
    #ret += f' & {stats['gbOVH']:.3f} & {stats['evOVH']:.3f} & {stats['ctOVH']:.2f}'
    ret += f' & {stats['ctOVH']:.2f}'
    ret += f' \\\ \hline'
    return ret

def test_circuit(benchmark,filename,num_of_trials=10):
    with open('text.txt', 'r') as file: data = file.read()
    stream = ''.join(format(ord(char), '08b') for char in data)
    with open(f'circuits/{benchmark}/{filename}', 'r') as file:
        txt = file.read()
        if benchmark == 'ps':
            txt = re.sub(r'\b(\d+)\b', r'w\1', txt) 
            circuit,_ = ps_compile(txt)
        else:
            circuit = bf_compile(txt)
        
        ilen=len(circuit.inputs)
        olen=len(circuit.outputs)
        slen = len(stream)
        ets = {'evHGG':[], 'evAOG':[], 'gbHGG':[], 'gbAOG':[], 'ctHGG':[], 'ctAOG':[]}         
        hgg = HGGarbler(circuit)
        aog = AuthOrGarbler(circuit)

        for i in range(num_of_trials):
            sidx = random.randint(0, slen - 1)
            inpt = stream[sidx:sidx+ilen] if sidx+ilen<=slen else stream[sidx:]+stream[0:ilen-(slen-sidx)]
            
            circuit.reset()
            circuit.assign_bits(inpt)
            circuit.evaluate()
            ets['gbAOG'].append(aog.garble())
            ets['evAOG'].append(aog.evaluate())
            ets['ctAOG'].append(circuit.getCTsize())

            circuit.reset()
            circuit.assign_bits(inpt)
            circuit.evaluate()
            ets['gbHGG'].append(hgg.garble())
            ets['evHGG'].append(hgg.evaluate())
            ets['ctHGG'].append(circuit.getCTsize())
        
        stats = {}
        for lbl in ['gbHGG','evHGG','ctHGG', 'gbAOG', 'evAOG', 'ctAOG']:
            m,d = estimate_distribution(ets[lbl])
            stats[lbl] = m
        
        stats['gbOVH'] = 100*(stats['gbHGG']-stats['gbAOG'])/stats['gbHGG']
        stats['evOVH'] = 100*(stats['evHGG']-stats['evAOG'])/stats['evHGG']
        stats['ctOVH'] = 100*(stats['ctHGG']-stats['ctAOG'])/stats['ctHGG']
        return stats
    
def crypto(filename,msglen,keylen,keyfirst=True,GarblerClass=AuthOrGarbler):
    with open('text.txt', 'r') as file: msg = file.read()
    msg = msg[0:int(msglen/8)]
    bin_msg = ''.join(format(ord(char), '08b') for char in msg)
    bin_key=''.join(random.choice('01') for _ in range(keylen))
    print(f'message:{msg}')
    print(f'key:{hex(int(bin_key,2))}')
    input_bits = bin_key + bin_msg if keyfirst else bin_msg + bin_key
    res = bf_task(filename,input_bits,GarblerClass)
    print(f'result= {hex_to_ascii(res)}')

def FP64(filename,val1,val2,GarblerClass=AuthOrGarbler):
    x = float64_to_binary(val1)
    y = float64_to_binary(val2)
    input_bits = x + y
    rstr = bf_task(filename,input_bits,GarblerClass)
    print(f'result={hex_to_float64(rstr)}')

def arithmetic64(filename,val1,val2,GarblerClass=AuthOrGarbler):
    num = (val2<<64)| val1
    input_bits = bin(num)[2:].zfill(128)
    rstr = bf_task(filename,input_bits,GarblerClass)
    print(f'result={int(rstr,16)}')

def mono(filename,val,input_len,GarblerClass=AuthOrGarbler):
    input_bits = bin(val)[2:].zfill(input_len)
    res = bf_task(filename,input_bits,GarblerClass)
    print(f'result={res}')

def bf_task(filename,input_bits,GarblerClass):
    with open(f'circuits/{filename}', 'r') as file:
        txt = file.read()
        circuit = bf_compile(txt)
        circuit.assign_bits(input_bits)
        circuit.evaluate()
        garbler = GarblerClass(circuit)
        elapsedGB = garbler.garble()
        elapsedEV = garbler.evaluate()
        print(circuit.getReport())
        print(f'Garbling ES:{elapsedGB}, Evaluation ES: {elapsedEV}, CT size: {circuit.getCTsize()}')
        return circuit.get_garbled_output_str_hex()

def ps_task():
    name='input.txt'
    with open(f'circuits/{name}', 'r') as file:
        txt = file.read()
        txt = re.sub(r'\b(\d+)\b', r'w\1', txt)

    circuit,input_map = ps_compile(txt)
    ilen = len(circuit.inputs)
    for x in range(pow(2,ilen)):
        circuit.reset()
        xstr = f'{x:0{ilen}b}' 
        circuit.assign_bits(xstr)
        circuit.evaluate()
        garbler = AuthOrGarbler(circuit)
        garbler.garble()
        garbler.evaluate()
        print(f'input={xstr}, output={circuit.get_garbled_output_str_hex()}')
    circuit.draw(name.split('.')[0])
    
if __name__ == "__main__":
    os.system('clear')
    #filename='and8.txt'
    #stats = test_circuit(filename,1)
    #print(to_latex(filename.split('.')[0],stats) + '\n')
    #print(test('bfCrypto'))
    #test_circuit('FP-mul.txt',2)
    ps_task()
    #mono('zero_equal.txt',12,64,HGGarbler)
    #mono('Keccak_f.txt',0x43aa841bde943853497583598,1600,HGGarbler)
    #arithmetic64('adder64.txt',6,5,AuthOrGarbler)
    #FP64('FP-mul.txt',6.0,5.0,AuthOrGarbler)
    #arithmetic64('mult2_64.txt',20,30,AuthOrGarbler)
    #arithmetic64('sdiv64.txt',56789,23490,AuthOrGarbler)
    #crypto('aes128.txt',msglen=128,keylen=128,keyfirst=True,GarblerClass=AuthOrGarbler)
    #crypto('aes256.txt',msglen=128,keylen=256,keyfirst=True,GarblerClass=AuthOrGarbler)
    #crypto('sha256.txt',msglen=512,keylen=256,keyfirst=False,GarblerClass=HGGarbler)
    #crypto('sha512.txt',msglen=1024,keylen=512,keyfirst=False,GarblerClass=HGGarbler)

