from helper import *
from garbling import *
from graphviz import Digraph
import networkx as nx
from schemdraw.parsing import logicparse

mnl = 0 #maximum name length 

class Pin:
    def __init__(self,name, value):
        self.name = name
        self.value = value
        self.hc_value = None #hardcoded value
        self.garbled_value = None
        self.tags = []
        self.ciphertext = None
    
    def __repr__(self):
        assert(len(self.tags) in [0, 2])
        if len(self.tags) == 2:
            return f'0:{tagtostr(self.tags[0])}, 1:{tagtostr(self.tags[1])}, gv:{'?' if self.garbled_value == None else tagtostr(self.garbled_value)}, v:{'?' if self.value == None else self.value}'
        else: return f'{self.name}:{'?' if self.value == None else self.value}'

    def reset(self):
        self.garbled_value = None
        self.tags = []
        self.ciphertext = None
    
    def set(self,val):
        if self.hc_value == None:self.value = val
        else : self.value = self.hc_value

class Gate:
    def __init__(self,type:str,inputs,output_name:str):
        self.type = type
        self.garbled_type = None
        self.inpins = [Pin(name,None) for name in inputs]
        self.outpin = Pin(output_name,None)
        self.name = output_name
        if len(self.inpins) != self.fanin(): raise Exception('invalid gate ' + repr(self))
    
    def __repr__(self):
        ins = ' ; '.join(f'<{pin}>' for pin in self.inpins)
        return f'<{self.outpin}> = {self.type}({ins}) => {self.garbled_type}'
        
    def evaluate(self):
        if len(self.inpins) != self.fanin(): raise Exception('invalid gate ' + repr(self))
        for pin in self.inpins:
            if pin.value == None:raise Exception('not evaluated pin ' + repr(pin))

        match self.type:
            case "AND": self.outpin.value = int(all(pin.value for pin in self.inpins))
            case "OR":  self.outpin.value = int(any(pin.value for pin in self.inpins))
            case "XOR": self.outpin.value = int(sum(pin.value for pin in self.inpins)%2 == 1)
            case "NOT": self.outpin.value = 1 - self.inpins[0].value
    
    def fanin(self):
        match self.type:
            case 'NOT':return 1
            case 'AND':return 2
            case 'XOR':return 2
            case _ : return 0

    def reset(self):
        self.garbled_type = None
        for pin in self.inpins:
            pin.reset()
        self.outpin.reset()

class Circuit:
    def __init__(self, gates): #gates:[Gate]
        def get_index(lst,name): return next((i for i, obj in enumerate(lst) if obj.name == name), -1)
        self.gates = self.__preprocess(gates)
        self.pins_map = self.__generate_wire_connection_map() #wire_map: {"pin_name":[connected TO gates]}

        self.inputs = self.__find_inputs()
        self.outputs = self.__find_outputs()
        self.gates = self.__topsort()
        
        #wiring the circuit via pointers
        for gate in self.gates:
            for igate in self.pins_map[gate.name]: # The gate is connected to igate
                idx = get_index(igate.inpins, gate.name)
                igate.inpins[idx] = gate.outpin
            for pin in gate.inpins:
                if pin.name in self.inputs:
                    idx = get_index(gate.inpins,pin.name)
                    gate.inpins[idx] = self.inputs[pin.name]

    def __preprocess(self,gates):
        def get_index(sett,name): return next((obj for obj in sett if obj.name == name), None)
        ret =[]
        irrgates=set()
        for gate in gates:
            if gate.fanin() == 2:
                if gate.inpins[0].name == gate.inpins[1].name:
                    irrgates.add(gate)
                    continue
            for pin in gate.inpins:
                irgate = get_index(irrgates,pin.name)
                if irgate != None:
                    if irgate.type == 'XOR': pin.hc_value = 0 #connect the pin to the ground
                    else: pin.name = irgate.inpins[0].name
            ret.append(gate)
        return ret
    
    def __repr__(self):
        return ''.join([str(g)+'\n' for g in self.gates])
    
    def __generate_wire_connection_map(self):
        m = {g.name:[] for g in self.gates}
        for g in self.gates:
            for pin in g.inpins:
                if not pin.name in m: m[pin.name] = [g]
                else: m[pin.name].append(g)
        return m
    
    def __find_inputs(self):
        global mnl
        outs={g.outpin.name for g in self.gates}
        ins = {}
        for gate in self.gates:
            for pin in gate.inpins:
                if pin.name not in outs: ins[pin.name] = pin
                mnl = max(mnl, len(pin.name))
        return ins
    
    def __find_outputs(self):
        ins={pin.name for gate in self.gates for pin in gate.inpins}
        outs= {}
        for gate in self.gates:
            if not gate.outpin.name in ins:
                outs[gate.outpin.name] = gate.outpin
        return outs

    def __topsort(self):
        G = nx.DiGraph()
        edges = []
        G.add_nodes_from(self.gates)
        for gate in self.gates:
            gates = self.pins_map[gate.outpin.name]
            edges.extend([(gate,g) for g in gates])
        G.add_edges_from(edges)
        topo_sort = list(nx.topological_sort(G))
        return topo_sort

    def assign(self, inputs): #inputs:{"wire_name":0 or 1}
        for iname,ivalue in inputs.items():
            if iname in self.inputs: self.inputs[iname].set(ivalue)

    def assign_bits(self,bits):
        i=0
        length = len(self.inputs)
        for name in sorted(self.inputs.keys(),key=custom_sort_key,reverse=True):
            self.inputs[name].set(int(bits[i]))
            if self.inputs[name].hc_value == None:i+=1

    def get_input_str(self):
        ret=''
        for name in sorted(self.inputs.keys(),key=custom_sort_key,reverse=True):
            if self.inputs[name].hc_value == None:
                ret += f'{self.inputs[name].value}'
        ret = hex(int(ret,2))
        return ret
    
    def get_output_str(self):
        ret=''
        for w in sorted(self.outputs.keys(),key=custom_sort_key,reverse=True):
            ret += f'{self.outputs[w].value}'
        ret = hex(int(ret,2))
        return ret
    
    def get_garbled_output_str_bits(self):
        ret=''
        for w in sorted(self.outputs.keys(),key=custom_sort_key):
            v = 0 if self.outputs[w].garbled_value == self.outputs[w].tags[0] else 1
            ret += f"{w}= {v}:{tagtostr(self.outputs[w].garbled_value)} in <0:{tagtostr(self.outputs[w].tags[0])},1:{tagtostr(self.outputs[w].tags[1])}>\n"
        return ret
    
    def get_garbled_output_str_hex(self):
        res=''
        for w in sorted(self.outputs.keys(),key=custom_sort_key,reverse=True):
            res+= '0' if self.outputs[w].garbled_value == self.outputs[w].tags[0] else '1'
        return hex(int(res,2))

    def evaluate(self): 
        for gate in self.gates:
            gate.evaluate()     

    def getCTsize(self):
        cts = set()
        for gate in self.gates: 
            for ipin in gate.inpins:
                cts.add(ipin.ciphertext)
            cts.add(gate.outpin.ciphertext)
        return len(cts)

    def getReport(self):
        rep ={'HG0':0, 'HG1a':0,'HG1b':0, 'HG2':0, 'FreeXOR2':0, 'FreeXOR1':0, 'FreeXOR0':0, 'ITAND':0, 'ITXOR':0, 'NOTF':0, 'NOTB':0}
        for gate in self.gates:
            rep[gate.garbled_type] += 1
        return rep

    def draw(self,name):
        dot = Digraph()
        dot.attr(rankdir='LR', splines='spline') #splines='ortho'
        dot.attr('edge', arrowhead='none')
        ploted = set()
        for g in self.gates:
            if not g.name in ploted: 
                lbl = g.garbled_type if g.garbled_type != None else ''
                dot.node(g.name, label=lbl, shape='none', image=f'icons/{g.type}.png')
                ploted.add(g.name) 
        
            for pin in g.inpins:
                if not pin.name in ploted:
                    dot.node(pin.name, label=pin.name, shape='point')
                    ploted.add(pin.name) 
                if pin.name in self.inputs:
                    dot.edge(pin.name, g.name, label=pin.name)
                else: dot.edge(pin.name, g.name,dir='forward')
            
            oname = g.outpin.name
            
            if oname in self.outputs:
                tmp_name = f'{oname}_tt'
                if not tmp_name in ploted: 
                    dot.node(tmp_name, label=oname, shape='point')
                    ploted.add(tmp_name) 
                dot.edge(g.name, tmp_name,label=oname)
            
        dot.render(name, format='png', cleanup=True)
    
    def draw2(self,name):
        strs = {}
        def tostr(gate):
            inputs = []
            for i in gate.inpins:
                if not i.name in strs: inputs.append(i.name)
                else: inputs.append(f'({strs[i.name]})')
            if gate.fanin() == 1:
                out = f'{gate.type} {inputs[0]}'
            elif gate.fanin() == 2:
                out = f'{inputs[0]} {gate.type} {inputs[1]}'
            else: raise Exception('not supported gate ' + repr(gate))
            strs[gate.outpin.name] = out
            return out 

        for gate in self.gates:
            tostr(gate)
        g = strs[self.gates[-1].outpin.name]
        g = g.lower()
        d = logicparse(g, outlabel='$y$')
        
        d.save(f'{name}.png')
        d.draw()

    def reset(self):
        for gate in self.gates:
            gate.reset()