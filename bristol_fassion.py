# Line 1: num_of_gates number_of_wires (Ex: 127 191)
# Line 2: num_of_inputs length_of_each_input  (Ex: 2 64 64)
# Line 3: num_of_outputs length_of_each_output (Ex: 1 64)
# Line 4 to end: list of gates topologically ordered
# Each gate: num_of_inputs num_of_outputs list_of_inputs list_of_outputs gate_type (Ex: 2 1 3 4 5 XOR is w_5 = XOR(w_3,w_4))
# https://nigelsmart.github.io/MPC-Circuits/

from circuits import Gate, Circuit

class bfParser:
    def __init__(self):
        pass

    def parse_gate(self,gate_str):
        parts = gate_str.split()
        num_inputs = int(parts[0])
        num_outputs = int(parts[1])
        if len(parts) != num_inputs+num_outputs+3:
            raise Exception('invalid format for the gate ' + repr(gate_str))
        
        if num_outputs != 1: raise Exception('not supported gate with more than 1 output pin ' + repr(gate_str))

        inputs = [f'w_{x}' for x in parts[2:2 + num_inputs]]
        output = f'w_{parts[-2]}'
        type = parts[-1]
        if type == 'INV': type = 'NOT'
        if type in ['EQ', 'EQW' ]:raise Exception('not supported gate ' + repr(gate_str))
        
        if type in ['XOR', 'AND', 'OR' ]:
            if num_inputs != 2: raise Exception('not supported gate ' + repr(gate_str))
            if inputs[0] == inputs[1]: print('irregular gate ' + repr(gate_str))

        return Gate(type,inputs,output)
    
    def parse(self,txt):
        i = 0
        gates = []
        for line in txt.splitlines():
            if line.isspace() or not line: continue
            match i:
                case 0:
                    parts = line.split()
                    num_gates = int(parts[0])
                    num_wires = int(parts[1])
                case 1:
                    parts = line.split()
                    num_inputs = int(parts[0])
                    lengths = [int(x) for x in parts[1:-1]]
                case 2:
                    parts = line.split()
                    num_outputs = int(parts[0])
                    lengths = [int(x) for x in parts[1:-1]]
                case _:
                    if line.startswith("#"):continue
                    gates.append(self.parse_gate(line))
            i +=1
        return Circuit(gates)

def bf_compile(txt):
    return bfParser().parse(txt)