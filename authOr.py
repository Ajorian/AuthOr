import time
from circuits import *

class AuthOrGarbler:
    def __init__(self,circuit):
        self.circuit = circuit
    
    def garble(self):
        t1 = time.perf_counter()
        for gate in self.circuit.gates: #forward pass
            self.gbFwGate(gate)
        
        for gate in reversed(self.circuit.gates): #backward pass
            if gate.garbled_type in ["ITAND", "ITXOR", "NOTB"] :
                self.gbBwGate(gate)
        t2 = time.perf_counter()
        return t2-t1

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
        
        if W_a == None or (W_b == None and gate.fanin() == 2): raise Exception('ungarbled gate ' + repr(gate))
        
        match gate.garbled_type:
            case 'ITAND':W_i = EvITAND(W_a,W_b,w_a,w_b)
            case 'ITXOR':W_i = EvITXOR(W_a,W_b)
            case 'FreeXOR0':W_i = EvFreeXOR0(W_a,W_b)
            case 'FreeXOR1':W_i = EvFreeXOR1(W_a,W_b)
            case 'FreeXOR2':W_i = EvFreeXOR2(W_a,W_b)
            case 'HG0':W_i = EvHG0(gate.name,W_a,W_b,w_a,w_b)
            case 'HG1a':W_i = EvHG1(gate.name,W_a,W_b,w_a,w_b)
            case 'HG1b':W_i = EvHG1(gate.name,W_b,W_a,w_b,w_a)
            case 'HG2':W_i = EvHG2(gate.name,F,W_a,W_b,w_a,w_b)
            case 'NOTF':W_i = EvNOT(W_a)
            case 'NOTB':W_i = EvNOT(W_a)
            case _: raise Exception('invalid grabled gate type ' + repr(gate.garbled_type))

        gate.outpin.garbled_value = W_i 
        if not W_i in gate.outpin.tags: raise Exception('invalid grabled tag ' + repr(gate))
        
        ev_val = 0 if W_i == gate.outpin.tags[0] else 1
        if ev_val != gate.outpin.value: raise Exception('invalid evaluated value ' + repr(gate))

    def gbFwGate(self,gate):
        input_tags = [pin.tags for pin in gate.inpins]
        if len(input_tags)!= gate.fanin() : raise Exception('invalid number of pins ' + repr(gate))
        
        W_a,*rest = input_tags
        W_b = rest[0] if rest else None
        W_i = gate.outpin.tags 
        if len(W_i) !=0 : raise Exception('invalid forward garbling ' + repr(gate))
        
        for pin in gate.inpins:
            if pin.value is None: raise Exception('unevaluated pin ' + repr(pin))
        
        has_common_input = any(len(self.circuit.pins_map[pin.name]) > 1 for pin in gate.inpins) # at least one of inputs is common with another gate (having branch)
        gate.garbled_type = DetermineGarbleType(gate.type, W_a, W_b, has_common_input)
        
        match gate.garbled_type:
            case 'ITAND':return
            case 'ITXOR':return
            case 'NOTB':return
            case 'FreeXOR0':
                W_a0,W_b0,W_i0 = GbFreeXOR0()
                W_a.append(W_a0)
                W_a.append(XOR(W_a0,delta))
                W_b.append(W_b0)
                W_b.append(XOR(W_b0,delta))
            case 'FreeXOR1':
                if len(W_a)>0:
                    W_b0,W_i0 = GbFreeXOR1(W_a[0])
                    W_b.append(W_b0)
                    W_b.append(XOR(W_b0,delta))
                else:
                    W_a0,W_i0 = GbFreeXOR1(W_b[0])
                    W_a.append(W_a0)
                    W_a.append(XOR(W_a0,delta))
            case 'FreeXOR2':
                W_i0 = GbFreeXOR2(W_a[0], W_b[0])
            case 'HG0':
                W_a0,W_b0,W_i0 = GbHG0(gate.name, delta)
                W_a.append(W_a0)
                W_a.append(XOR(W_a0,delta))
                W_b.append(W_b0)
                W_b.append(XOR(W_b0,delta))
            case 'HG1a':
                W_b0,W_i0 = GbHG1(gate.name, W_a[0], delta)
                W_b.append(W_b0)
                W_b.append(XOR(W_b0,delta))
            case 'HG1b':
                W_a0,W_i0 = GbHG1(gate.name, W_b[0], delta)
                W_a.append(W_a0)
                W_a.append(XOR(W_a0,delta))
            case 'HG2':
                F, W_i0 = GbHG2(gate.name, W_a[0], W_b[0], delta)
                gate.outpin.ciphertext = F
            case 'NOTF':
                if len(W_a)!=2:
                    rt = randtag() 
                    W_a.append(rt)
                    W_a.append(XOR(rt,delta))
                W_i0 = GbFwNOT(W_a[0],delta)
            case _: raise Exception('invalid grabled gate type ' + repr(gate.garbled_type))
        W_i.append(W_i0)
        W_i.append(XOR(W_i0,delta))

    def gbBwGate(self,gate):
        if len(gate.outpin.tags)== 0:
            gate.outpin.tags.append(randtag())
            gate.outpin.tags.append(randtag())

        if len(gate.outpin.tags)!= 2: raise Exception('invalid number of pin ' + repr(gate.output[1].tags))
        W_i0, W_i1 = gate.outpin.tags 
        
        tags = [pin.tags for pin in gate.inpins]
        if len(tags)!= gate.fanin(): raise Exception('invalid number of pin' + repr(tags))
        
        W_a,*rest = tags
        W_b = rest[0] if rest else None

        match gate.garbled_type:
            case 'ITAND':
                W_a0,W_a1,W_b0,W_b1 = GbITAND(W_i0,W_i1)
            case 'ITXOR':
                W_a0,W_a1,W_b0,W_b1 = GbITXOR(W_i0,W_i1)
            case 'NOTB':
                W_a0,W_a1 = GbBwNOT(W_i0,W_i1)

        W_a.append(W_a0)
        W_a.append(W_a1)
        if gate.fanin()>1:
            W_b.append(W_b0)
            W_b.append(W_b1)
