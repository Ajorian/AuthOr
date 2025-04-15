from circuits import *
from helper import *
import time

class HGGarbler:
    def __init__(self,circuit):
        self.circuit = circuit
    
    def garble(self):
        t1 = time.perf_counter()
        for gate in self.circuit.gates:
            self.gbGate(gate)  

        t2 = time.perf_counter()
        return t2-t1          

    def gbGate(self,gate):
        input_tags = [pin.tags for pin in gate.inpins]
        if len(input_tags)!= gate.fanin() : raise Exception('invalid number of pins ' + repr(gate))
        
        W_a,*rest = input_tags
        W_b = rest[0] if rest else None
        W_i = gate.outpin.tags
        if len(W_i) !=0 : raise Exception('invalid forward garbling ' + repr(gate))

        for pin in gate.inpins:
            if pin.value is None: raise Exception('unevaluated pin ' + repr(pin))
    
        if len(W_a) == 0:
            rt = randtag()
            W_a.append(rt)
            W_a.append(XOR(rt,delta))
        if gate.fanin()>1 and len(W_b) == 0:
            rt = randtag()
            W_b.append(rt)
            W_b.append(XOR(rt,delta))

        match gate.type:
            case 'AND':
                gate.garbled_type = 'HG2'
                F, W_i0 = GbHG2(gate.name, W_a[0], W_b[0], delta)
                gate.outpin.ciphertext = F
            case 'XOR':
                gate.garbled_type = 'FreeXOR2'
                W_i0 = GbFreeXOR2(W_a[0], W_b[0])
            case 'NOT':
                gate.garbled_type  = 'NOTF'
                W_i0 = GbFwNOT(W_a[0],delta)
        
        W_i.append(W_i0)
        W_i.append(XOR(W_i0,delta))

    def evaluate(self):
        t1 = time.perf_counter()
        for pin in self.circuit.inputs.values():
            if len(pin.tags) == 0: raise Exception('non garbled pin ' + repr(pin))
            if pin.value == None : raise Exception('no value assigned to pin ' + repr(pin))
            pin.garbled_value = pin.tags[pin.value]
        
        for gate in self.circuit.gates:
            self.evGate(gate)
        t2 = time.perf_counter()
        return t2-t1
    
    def evGate(self,gate):
        input_pins = [pin for pin in gate.inpins]
        if len(input_pins)!= gate.fanin(): raise Exception('invalid number of pins ' + repr(input_pins))

        W_a = input_pins[0].garbled_value
        w_a = input_pins[0].value
        W_b = input_pins[1].garbled_value if gate.fanin()>1 else None
        w_b = input_pins[1].value if gate.fanin()>1 else None
        F = gate.outpin.ciphertext
    
        match gate.garbled_type:
            case 'FreeXOR2':W_i = EvFreeXOR2(W_a,W_b)
            case 'HG2':W_i = EvHG2(gate.name,F,W_a,W_b,w_a,w_b)
            case 'NOTF':W_i = EvNOT(W_a)
            case _: raise Exception('invalid grabled gate type ' + repr(gate.garbled_type))
        
        gate.outpin.garbled_value = W_i 
        if not W_i in gate.outpin.tags: raise Exception('invalid grabled tag ' + repr(gate))
        
        ev_val = 0 if W_i == gate.outpin.tags[0] else 1
        if ev_val != gate.outpin.value: raise Exception('invalid evaluated value ' + repr(gate))