import scdf
import hamming
import sort
import utils

nbits = 32

class Bit(object):
    def __init__(self, val):
        self.val = val % 2
        
    def __mul__(self, other):
        return Bit((self.val * other.val) % 2)
        
    def __add__(self, other):
        return Bit((self.val + other.val) % 2)
    
def add_num_to_map(name, num, input_map):
    bin_rep = utils.to_bin(num, nbits)
    add_bin_str_to_map(name, bin_rep, input_map)

def add_bin_str_to_map(name, bin_str, input_map):
    for i in range(len(bin_str)):
        input_map['%s%d' % (name, i)] = Bit(bin_str[i])
        
def map_constant(constant):
    return Bit(constant)

def test_hamming_weight():
    bv = [1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
          1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0
    ]
    num_bits = len(bv)
    v = scdf.vect_input('v', num_bits)
    w = hamming.hamming_weight(v)

    input_map = {}
    add_bin_str_to_map('v', bv, input_map)

    weight_bits = []
    for i in range(len(w)):
        bit = scdf.eval_circuit(w[i], input_map, map_constant)
        weight_bits.append(bit.val)
    weight = utils.from_bin(weight_bits)
    print 'Hamming weight: ', weight
        
    reduced = map(scdf.reduce_depth, w)
    depths = map(scdf.compute_depth, reduced)
    print 'Depths of each output bit: ', depths

    deduplicated = map(scdf.deduplicate, reduced)
    print 'Number of gates: ',
    counts = map(scdf.count_gates, deduplicated)
    print sum(counts)

test_hamming_weight()
