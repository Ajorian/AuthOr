from helper import hash, XOR, randtag, tagtostr

def DetermineGarbleType(type, W_a, W_b, has_common_input): #common input
    if type == 'NOT': 
        if has_common_input or len(W_a) ==2: return 'NOTF'
        return 'NOTB'
    if len(W_a)==0 and len(W_b)==0 and not has_common_input: #Both are TypeS
        match type:
            case 'AND': return 'ITAND'
            case 'XOR': return 'ITXOR'
            case _: return None
    elif len(W_a)==2 and len(W_b)==2: #Both are of TypeD
        match type:
            case 'AND': return 'HG2'
            case 'XOR': return 'FreeXOR2'
            case _: return None
    elif len(W_a)==2 and len(W_b) ==0: #a is TypeD and b is not TypeD
        match type:
            case 'AND': return 'HG1a'
            case 'XOR': return 'FreeXOR1'
            case _: return None
    elif len(W_a)==0 and len(W_b) ==2: # b is TypeD and a is not TypeD
        match type:
            case 'AND': return 'HG1b'
            case 'XOR': return 'FreeXOR1'
            case _: return None
    elif has_common_input: # one of them is TypeM and the othe one is not TypeD
        match type:
            case 'AND': return 'HG0'
            case 'XOR': return 'FreeXOR0'
            case _: return None
    return None

def GbHG2(i, W_a0, W_b0, delta):
    W_i0 = hash(i, W_a0)
    F = XOR(hash(i,W_a0),XOR(hash(i, XOR(W_a0,delta)),W_b0))
    return (F,W_i0)

def GbHG1(i, W_a0, delta):
    W_i0 = hash(i, W_a0)
    W_b0 = XOR(W_i0,hash(i,XOR(W_a0,delta)))
    return (W_b0,W_i0)

def GbHG0(i, delta):
    W_a0 = randtag()
    W_i0 = hash(i, W_a0)
    W_b0 = XOR(W_i0,hash(i,XOR(W_a0,delta)))
    return (W_a0,W_b0,W_i0)

def EvHG2(i,F,W_a, W_b, w_a, w_b):
    if w_a == 0:
        W_i = hash(i,W_a)
    else:
        W_i = XOR(XOR(hash(i,W_a),W_b),F)
    return W_i

def EvHG1(i, W_a, W_b, w_a, w_b):
    if w_a == 0: W_i = hash(i,W_a)
    else: W_i = XOR(hash(i,W_a),W_b)
    return W_i

def EvHG0(i, W_a, W_b, w_a, w_b):
    if w_a == 0: W_i = hash(i,W_a)
    else: W_i = XOR(hash(i,W_a),W_b)
    return W_i

def GbFreeXOR2(W_a0, W_b0):
    W_i0 = XOR(W_a0,W_b0)
    return W_i0

def GbFreeXOR1(W_a0):
    W_b0 = randtag()
    W_i0 = XOR(W_a0,W_b0)
    return (W_b0,W_i0)

def GbFreeXOR0():
    W_a0 = randtag()
    W_b0 = randtag()
    W_i0 = XOR(W_a0,W_b0)
    return (W_a0,W_b0,W_i0)

def EvFreeXOR2(W_a,W_b):
    return XOR(W_a,W_b)

def EvFreeXOR1(W_a,W_b):
    return XOR(W_a,W_b)

def EvFreeXOR0(W_a,W_b):
    return XOR(W_a,W_b)

def GbITAND(W_i0, W_i1):
    W_a0 = W_i0
    W_b0 = W_i0
    W_a1 = randtag()
    W_b1 = XOR(W_a1,W_i1)
    return (W_a0,W_a1,W_b0,W_b1)

def EvITAND(W_a, W_b,w_a,w_b):
    if w_a == 0: W_i = W_a
    elif w_b == 0: W_i = W_b
    else: W_i = XOR(W_a,W_b)
    return W_i

def GbITXOR(W_i0, W_i1):
    W_a1 = randtag()
    W_b1 = XOR(W_a1,W_i0)
    W_a0 = XOR(W_b1,W_i1)
    W_b0 = XOR(W_a1,W_i1)
    return (W_a0,W_a1,W_b0,W_b1)

def EvITXOR(W_a,W_b):
    return XOR(W_a,W_b)

def GbFwNOT(W_a0,delta):
   return XOR(W_a0,delta)

def GbBwNOT(W_i0,W_i1):
   return (W_i1,W_i0)

def EvNOT(W_a):
    return W_a