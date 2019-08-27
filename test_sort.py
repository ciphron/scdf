import scdf
import utils
import sort

class BinVector:
    def __init__(self, elems):
        self.num_slots = len(elems)
        self.elems = list(elems)
        
    def __lshift__(self, num_places):
        return BinVector(self.elems[num_places:] + self.elems[:num_places])

    def __rshift__(self, num_places):
        return BinVector(self.elems[-num_places:] + self.elems[:self.num_slots - num_places])

    def __mul__(self, other):
        return BinVector(map(lambda (x, y): (x * y) % 2, zip(self.elems, other.elems)))

    def __add__(self, other):
        return BinVector(map(lambda (x, y): (x + y) % 2, zip(self.elems, other.elems)))


# number of bits in each element
nbits = 8

# number of elements in the array to sort
N = 8

# dimension of the bin vectors
nslots = 8
def map_constant(constant):
    return BinVector([constant] * nslots)

def add_num_to_map(name, num, input_map):
    bin_rep = utils.to_bin(num, nbits)

    for i in range(nbits):
        vect = [0] * nslots
        vect[0] = bin_rep[i]
        input_map['%s%d' % (name, i)] = BinVector(vect)

def add_array_to_map(name, array, input_map):
    for i in range(len(array)):
        add_num_to_map('%s%d' % (name, i), array[i], input_map)

def unpack_array(elements):
    if len(elements) == 0:
        return []

    array = []
    
    for element in elements:
        bits = []
        for b in element:
            bits.append(b.elems[0])

        array.append(utils.from_bin(bits))
    return array


# A sorting network for 5 elements
#sorting_network = [(1, 2), (4, 3), (2, 3), (0, 2), (1, 4), (2, 4), (3, 4), (0, 2), (0, 1)]

X = scdf.array_input('X', N, nbits)
Y = sort.direct_sort_p(X)

input_map = {}
add_array_to_map('X', [5, 3, 2, 4, 1, 7, 8, 6], input_map)


elements = []
max_depth = 0
gate_count = 0
for y in Y:
    element = []
    for b in y:
        b = scdf.reduce_depth(b)
        d = scdf.compute_depth(b)
        if d > max_depth:
            max_depth = d
        gate_count += scdf.count_gates(b, set([scdf.Gate.ADD, scdf.Gate.MUL]))
        element.append(scdf.eval_circuit(b, input_map, map_constant))
    elements.append(element)

print 'Sorted Array:', unpack_array(elements)
print 'Max Depth:', max_depth
print 'Gate Count:', gate_count

