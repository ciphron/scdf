class Circuit(object):
    def __add__(self, other):
        return Gate(Gate.ADD, self, other)

    def __mul__(self, other):
        return Gate(Gate.MUL, self, other)

    def __lshift__(self, num_places):
        return Gate(Gate.SHIFT_LEFT, self, num_places)

    def __rshift__(self, num_places):
        return Gate(Gate.SHIFT_RIGHT, self, num_places)


class Gate(Circuit):
    ADD = 1
    MUL = 2
    SHIFT_LEFT = 3
    SHIFT_RIGHT = 4

    def __init__(self, gate_type, left, right):
        self.is_terminal = False
        self.gate_type = gate_type
        self.left = left
        self.right = right
    

class Constant(Circuit):
    def __init__(self, value):
        self.is_terminal = True
        self.is_constant = True
        self.value = value

    def __mul__(self, other):
        if self.value == 0:
            return self
        if self.value == 1:
            return other
        return super(Constant, self).__mul__(other)

    def __add__(self, other):
        if self.value == 0:
            return other
        return super(Constant, self).__add__(other)

class Input(Circuit):
    def __init__(self, name):
        self.is_terminal = True
        self.is_constant = False
        self.name = name


def eval_circuit(circ, input_map, map_constant, eval_map={}):
    if circ in eval_map:
        return eval_map[circ]

    if circ.is_terminal:
        if circ.is_constant:
            value = map_constant(circ.value)
            eval_map[circ] = value
            return value
        if circ.name not in input_map:
            raise Exception('Input not found in input map')
        eval_map[circ] = input_map[circ.name]
        return input_map[circ.name]
    elif circ.gate_type is Gate.ADD or circ.gate_type is Gate.MUL:
        left = eval_circuit(circ.left, input_map, map_constant, eval_map)
        right = eval_circuit(circ.right, input_map, map_constant, eval_map)
        
        if circ.gate_type == Gate.ADD:
            s = left + right
            eval_map[circ] = s 
            return s
        elif circ.gate_type == Gate.MUL:
            p = left * right
            eval_map[circ] = p
            return p
        else:
            raise Exception('Unknown gate type')
    else:
        value = eval_circuit(circ.left, input_map, map_constant, eval_map)
        if circ.gate_type is Gate.SHIFT_LEFT:
            value <<= circ.right
        else:
            value >>= circ.right
        eval_map[circ] = value
        return value        
        

def construct_mul_tree(operands):
    in_operands = operands
    out_operands = []

    depths = {}

    for circ in in_operands:
        depths[circ] = compute_depth(circ)
        
    in_operands.sort(key=lambda x: depths[x])

    while len(in_operands) >= 2:
        while len(in_operands) != 0:
            if len(in_operands) >= 2:
                left = in_operands[0]
                right = in_operands[1]
                gate = Gate(Gate.MUL, left, right)
                out_operands.append(gate)
                in_operands = in_operands[2:]
            else:
                out_operands.append(in_operands[0])
                in_operands = in_operands[1:]
        in_operands = out_operands
        out_operands = []
    circ = in_operands[0]
    depth = compute_depth(circ, depths)
    if not circ.right.is_terminal:
        r = circ.right.right
        if r in operands and depth > (compute_depth(r, depths) + 1):
            circ.right = circ.right.left
            circ = Gate(Gate.MUL, circ, r)
            found_operands = []

    return circ


def reduce_depth(circ, reduced={}, mulchain=False, operands=[]):
    if circ in reduced and not mulchain:
        return reduced[circ]

    if not circ.is_terminal and circ.gate_type is Gate.MUL:
        if not mulchain:
            mul_operands = []
            reduce_depth(circ.left, reduced, True, mul_operands)
            reduce_depth(circ.right, reduced, True, mul_operands)

            noperands = len(mul_operands)
            for i in range(noperands):
                mul_operands[i] = reduce_depth(mul_operands[i],
                                               reduced)            
            new_circ = construct_mul_tree(mul_operands)
            if compute_depth(circ) < compute_depth(new_circ):
                reduced[circ] = circ
                return circ
            else:
                reduced[circ] = new_circ
                return new_circ
        else:
            reduce_depth(circ.left, reduced, mulchain, operands)
            reduce_depth(circ.right, reduced, mulchain, operands)
    elif mulchain:
        operands.append(circ)
    elif not circ.is_terminal:
        left = reduce_depth(circ.left, reduced)
        if circ.gate_type is Gate.ADD:
            right = reduce_depth(circ.right, reduced)
        else:
            right = circ.right
        gate = Gate(circ.gate_type, left, right)
        reduced[circ] = gate
        return gate
        
    else:
        reduced[circ] = circ
    return circ

def is_shift(circ):
    return not circ.is_terminal and circ.gate_type is Gate.SHIFT_LEFT or\
        circ.gate_type is Gate.SHIFT_RIGHT
        

def count_gates(circ,
                gate_types=set([Gate.ADD, Gate.MUL, Gate.SHIFT_LEFT, Gate.SHIFT_RIGHT]),
                counted=set([])):
    if circ in counted or circ.is_terminal:
        return 0

    left_count = count_gates(circ.left, gate_types, counted)
    if not is_shift(circ):
        right_count = count_gates(circ.right, gate_types, counted)
    else:
        right_count = 0

    counted.add(circ)
    count = left_count + right_count
    if circ.gate_type in gate_types:
        count += 1
    return count
    

def print_circuit(circ):
    if circ.is_terminal:
        if circ.is_constant:
            print circ.value,
        else:
            print circ.name,
    else:
            print '(',
            print_circuit(circ.left)
            if circ.gate_type is Gate.MUL:
                print '*',
                print_circuit(circ.right)
            elif circ.gate_type is Gate.ADD:
                print '+',
                print_circuit(circ.right)
            elif circ.gate_type is Gate.SHIFT_LEFT:
                print ('<< ' + circ.right), 
            else:
                print ('>> ' + circ.right), 

            print ')',


def compute_depth(circ, depths={}):
    if circ in depths:
        return depths[circ]

    depth = 0
    if not circ.is_terminal:
        left_depth = compute_depth(circ.left, depths)
        if circ.gate_type is Gate.ADD or circ.gate_type is Gate.MUL:
            right_depth = compute_depth(circ.right, depths)
        else:
            right_depth = 0
        depth = max(left_depth, right_depth)
        if circ.gate_type is Gate.MUL:
            depth += 1
    depths[circ] = depth
    return depth

def compare_circuits(circ1, circ2):
    if not circ1.is_terminal:
        if circ2.is_terminal:
            return False
        if circ1.gate_type != circ2.gate_type:
            return False
        if is_shift(circ1):
            return compare_circuits(circ1.left, circ2.left) and circ1.right == circ2.right
        return (compare_circuits(circ1.left, circ2.left) and compare_circuits(circ1.right, circ2.right)) or \
               (compare_circuits(circ1.left, circ2.right) and compare_circuits(circ1.right, circ2.left))
    elif not circ2.is_terminal:
        return False
    else:
        if circ1.is_constant and circ2.is_constant:
            return circ1.value == circ2.value
        elif not circ1.is_constant and not circ2.is_constant:
            return circ1.name == circ2.name
    return False

def vect_input(name, dim):
    v = []
    for i in range(dim):
        v.append(Input('%s%d' % (name, i)))
    return v

def array_input(name, n, nbits):
    return [vect_input('%s%d' % (name, i), nbits) for i in range(n)]
