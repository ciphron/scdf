class Circuit(object):
    def __add__(self, other):
        return Gate(Gate.ADD, self, other)

    def __mul__(self, other):
        return Gate(Gate.MUL, self, other)

    def __lshift__(self, num_places):
        return Gate(Gate.SHIFT_LEFT, self, num_places)

    def __rshift__(self, num_places):
        return Gate(Gate.SHIFT_RIGHT, self, num_places)

    @property
    def is_terminal(self):
        pass


class Gate(Circuit):
    ADD = 1
    MUL = 2
    SHIFT_LEFT = 3
    SHIFT_RIGHT = 4

    def __init__(self, gate_type, left, right):
        self._gate_type = gate_type
        self._left = left
        self._right = right

    @property
    def is_terminal(self):
        return False

    @property
    def gate_type(self):
        return self._gate_type

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

class Terminal(Circuit):
    def __init__(self, is_constant):
        self._is_constant = is_constant

    @property
    def is_terminal(self):
        return True

    @property
    def is_constant(self):
        return self._is_constant
    

class Constant(Terminal):
    def __init__(self, value):
        super(Constant, self).__init__(True)
        self._value = value

    @property
    def value(self):
        return self._value

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

class Input(Terminal):
    def __init__(self, name):
        super(Input, self).__init__(False)
        self._name = name

    @property
    def name(self):
        return self._name


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
		marked = set()
		mul_operands_new = []
		for i in range(noperands):
                    if i not in marked:
                        mul_operands_new.append(mul_operands[i])
		    for j in range(i + 1, noperands):
			if compare_circuits(mul_operands[i], mul_operands[j]):
                            marked.add(j)
						
            new_circ = construct_mul_tree(mul_operands_new)
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

def expand(circ, exp={}):
    if circ in exp:
        return exp[circ]

    if circ.is_terminal:
        exp[circ] = circ
        return circ

    if circ.gate_type is not Gate.MUL:
        exp_circ = Gate(circ.gate_type, expand(circ.left, exp),
                        expand(circ.right, exp))
        exp[circ] = exp_circ
        return exp_circ

    left = expand(circ.left, exp)
    right = expand(circ.right, exp)
    exp_circ = insert_mul(left, right)
    exp[circ] = exp_circ
    return exp_circ


def is_product(circ):
    return circ.is_terminal or circ.gate_type is Gate.MUL

def insert_mul(multiplier, circ):
    if is_product(circ):
        if is_product(multiplier):
            return Gate(Gate.MUL, multiplier, circ)
        else:
            return insert_mul(circ, multiplier)
    elif not circ.is_terminal and circ.gate_type is Gate.ADD:
        return Gate(circ.gate_type, insert_mul(multiplier, circ.left),
                    insert_mul(multiplier, circ.right))
    return circ

def distribute(circ):
    if circ.is_terminal:
        return circ

    if circ.gate_type is not Gate.MUL:
        return circ

    left = circ.left
    right = circ.right

    add_gate = None
    multiplier = None
    if not left.is_terminal and left.gate_type is Gate.ADD:
        add_gate = left
        multiplier = right
    elif not right.is_terminal and right.gate_type is Gate.ADD:
        add_gate = right
        multiplier = left
    else:
        return circ

    add_left = Gate(Gate.MUL, multiplier, add_gate.left)
    add_right = Gate(Gate.MUL, multiplier, add_gate.right)

    return Gate(Gate.ADD, add_left, add_right)

def build_mul_operands(circ):
    if circ.is_terminal or circ.gate_type != Gate.MUL:
        return [circ]
    mul_operands_left = build_mul_operands(circ.left)
    mul_operands_right = build_mul_operands(circ.right)
    return mul_operands_left + mul_operands_right

def simplify(circ, simpl={}):
    if circ in simpl:
        return simpl[circ]

    if circ.is_terminal:
        simpl[circ] = circ
        return circ

    if circ.gate_type is not Gate.ADD:
        circ_simpl = Gate(circ.gate_type, simplify(circ.left, simpl),
                          simplify(circ.right, simpl))
        simpl[circ] = circ_simpl
        return circ_simpl

    left = simplify(circ.left)
    right = simplify(circ.right)

    if left.is_terminal or left.gate_type is not Gate.MUL or right.is_terminal \
       or right.gate_type is not Gate.MUL:
        circ_simpl = Gate(circ.gate_type, left,
                          right)
        simpl[circ] = circ_simpl
        return circ_simpl

    left_mul_operands = build_mul_operands(left)
    right_mul_operands = build_mul_operands(right)

    marked = set()
    new_left_mul_operands = []
    new_right_mul_operands = []
    common_operands = []

    for operand in left_mul_operands:
        matched = False
        for i in range(len(right_mul_operands)):
            if compare_circuits(operand, right_mul_operands[i]):
                marked.add(i)
                common_operands.append(operand)
                matched = True
        if not matched:
            new_left_mul_operands.append(operand)

    for i in range(len(right_mul_operands)):
        if i not in marked:
            new_right_mul_operands.append(right_mul_operands[i])

    if len(new_left_mul_operands) == 0:
        left = Constant(1)
    else:
        left = simplify(construct_mul_tree(new_left_mul_operands), simpl)

    if len(new_right_mul_operands) == 0:
        right = Constant(1)
    else:
        right = simplify(construct_mul_tree(new_right_mul_operands), simpl)
    common_tree = simplify(construct_mul_tree(common_operands), simpl)
    add_gate = Gate(Gate.ADD, left, right)
    mul_gate = Gate(Gate.MUL, add_gate, common_tree)
    simpl[circ] = mul_gate

    return mul_gate


def deduplicate(circ, subcircs=set()):
    if circ in subcircs:
        return circ

    for sc in subcircs:
        if compare_circuits(circ, sc):
            return sc

    if not circ.is_terminal:
        circ = Gate(circ.gate_type, deduplicate(circ.left, subcircs),
                    deduplicate(circ.right, subcircs))

    subcircs.add(circ)
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

