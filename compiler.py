import ast
from ast import *
from circuits import*

valid_gates =["AND", "XOR","NOT"]

class Compiler:
    def __init__(self):
        self.v_id =-1
        self.emu_id = 0

    def generate_name(self):
        self.v_id += 1
        return 'v' + str(self.v_id)

    def resolve(self,exp,genname):
        ret = []
        match exp:
            case Call(gatename,in_pins): #gate
                inputs = []
                gates = []
                for pin in in_pins: 
                    i_pin,gss = self.resolve(pin,None)
                    inputs.append(i_pin)
                    gates+= gss
                o_name = self.generate_name() if genname == None else genname
                return Name(o_name), gates + [Assign([Name(o_name)],Call(gatename,inputs))]
            
            case Name(x): #pin
                return exp,[]
                    
            case _:raise Exception('resolve error: ' + repr(exp))

    def explicate(self,c_ast):
        ret = []
        input_map = {}
        for stmt in c_ast.body:
            match stmt:
                case Expr(ast.Dict(keys, values)):  # dictionary
                    input_map = {}
                    for key, value in zip(keys, values):
                        if isinstance(key,Constant) and isinstance(value,Constant):
                            input_map[key.value] = value.value
                        else: raise Exception('resolve error: ' + repr(stmt))
        
                case Expr(gate):
                    o_pin,gates = self.resolve(gate,self.generate_name())
                    ret+= gates
                case Assign([Name(outname)], gate):
                    o_pin, gates = self.resolve(gate,outname)
                    ret+= gates
        return ret,input_map
    
    def generate_emname(self):
        ret = f't_eml{self.emu_id}'
        self.emu_id +=1
        return ret
    
    def emulate_gate(self,gatename,inputs,output):
        def handle_inputs(type,negate):
            gates = []
            i0 = inputs[0]
            if negate: 
                ii0 = self.generate_emname()
                gates.append(Gate("NOT",[i0],ii0))
                i0 = ii0
            for idx in range(1,len(inputs)):
                i1 = inputs[idx]
                if negate: 
                    ii1 = self.generate_emname()
                    gates.append(Gate("NOT",[i1],ii1))
                    i1 = ii1
                outpin = self.generate_emname()
                gates.append(Gate(type,[i0,i1],outpin))
                i0 = outpin
            return gates

        match gatename:
            case "AND":return handle_inputs("AND",False)
            case "XOR":return handle_inputs("XOR",False)
            case "NOR":return handle_inputs("AND",True)
            case "NAND": gates = handle_inputs("AND",False)   
            case "XNOR": gates = handle_inputs("XOR",False)
            case "OR": gates = handle_inputs("AND",True)
            case "BUFF": gates = [Gate("NOT",inputs,self.generate_emname())]
            case _: return None
        output = self.generate_emname()
        gates.append(Gate("NOT",[gates[-1].outpin.name],output))
        return gates

    def compile(self,txt):
        c_ast = ast.parse(txt)
        gates = []
        asignments,input_map = self.explicate(c_ast)
        for a in asignments:
            match a:
                case Assign([Name(output)],Call(Name(gatename),n_inputs)):
                    inputs = [n.id for n in n_inputs]
                    if len(inputs)>2 or gatename not in valid_gates:
                        gts = self.emulate_gate(gatename,inputs,output)
                        if gts == None: raise Exception('Unknown gate ' + repr(gatename))
                        for gt in gts: gates.append(gt)
                    else:
                        gates.append(Gate(gatename,inputs,output))
        return Circuit(gates),input_map

def ps_compile(txt):
    return Compiler().compile(txt)