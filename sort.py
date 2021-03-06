from base import *
import hamming
import math
import scdf

# Direct sort from https://eprint.iacr.org/2015/274.pdf
def direct_sort(X):
    N = len(X)
    log_n = int(math.ceil(math.log(N, 2)))
    M = create_matrix([N, N], zero)
    for i in range(N):
        for j in range(i + 1, N):
            M[i][j] = lt(X[i], X[j])
            M[j][i] = M[i][j] + one

    M = transpose(M)

    s = []
    for i in range(N):
        s.append(hamming.hamming_weight(M[i])[:-1])
    
    Y = [0] * N
    for i in range(N):
        Y[i] = [zero] * len(X[0])
        for j in range(N):
            z = eq(to_constant(i, log_n), s[j])
            for k in range(len(X[0])):
                Y[i][k] += z*X[j][k]

    return Y

# SIMD-optimized version of direct sort
def direct_sort_p(X):
    N = len(X)
    nbits = len(X[0])
    log_n = int(math.ceil(math.log(N, 2)))
    a = [zero] * nbits
    for j in range(nbits):
        elems = []
        for i in range(N):
            elems.append(X[i][j])
        a[j] = fill_slots_with_list(elems, N)

    M = []
    for i in range(N):
        x = []
        for j in range(nbits):
            x.append(fill_slots_with_elem(X[i][j], N))
        M.append(lt(x, a))

    s = hamming_weight(M)[:-1]

    zs = []
    ds = []

    Y = [0] * N
    for i in range(N):
        Y[i] = [zero] * len(X[0])
        c = to_bin(i, log_n)
        d = []
        for j in range(len(c)):
            if c[j] == 0:
                d.append(zero)
            else:
                d.append(one)
        z = eq(d, s)
        zs.append(z)
        for j in range(N):
            for k in range(len(X[0])):
                Y[i][k] += z*X[j][k]
            z <<= 1

    return Y

def sn_sort(sorting_network, elements):
    for (i, j) in sorting_network:
        elem_i = elements[i]
        elem_j = elements[j]
        is_lt = lt(elem_i, elem_j)
        min_elem = mux(is_lt, elem_j, elem_i)
        max_elem = mux(is_lt, elem_i, elem_j)
        elements[i] = min_elem
        elements[j] = max_elem

# This algorithm is due to Cetin, Doroz, Sunar and Savas
# Currently, we only have support for length 4 and length 8
# vectors
def hamming_weight(v):
    if len(v) == 4:
        result = [0] * 2
        s = v[0] + v[1] + v[2]
        result[0] = s + v[3]
        c1 = v[0]*v[1] + v[0]*v[2] + v[1]*v[2]
        c2 = s * v[3]
        result[1] = c1 + c2
    elif len(v) == 8:
        result = [0] * 3
        s1 = v[0] + v[1] + v[2]
        s2 = v[3] + v[4] + v[5]
        s3 = v[6] + v[7]
        s11 = s1 + s2 + s3
        result[0] = s11
        
        c1 = v[0]*v[1] + v[0]*v[2] + v[1]*v[2]
        c2 = v[3]*v[4] + v[3]*v[5] + v[4]*v[5]
        c3 = v[6]*v[7]
        
        s21 = c1 + c2 + c3
        c11 = s1*s2 + s1*s3 + s2*s3
        s22 = s21 + c11
        result[1] = s22

        c21 = c1*c2 + c1*c3 + c2*c3
        c22 = s21*c11
        s33 = c21 + c22
        result[2] = s33
    elif len(v) == 16:
        result = [zero] * 4
		
        s1 = v[0] + v[1] + v[2]
        s2 = v[3] + v[4] + v[5]
        s3 = v[6] + v[7] + v[8]
        s4 = v[9] + v[10] + v[11]
        s5 = v[12] + v[13] + v[14]
        s6 = v[15]
		
        s11 = s1 + s2 + s3
        s12 = s4 + s5 + s6
	result[0] = s11 + s12
		
	c1 = v[0]*v[1] + v[0]*v[2] + v[1]*v[2]
        c2 = v[3]*v[4] + v[3]*v[5] + v[4]*v[5]
        c3 = v[6]*v[7] + v[6]*v[8] + v[7]*v[8]
	c4 = v[9]*v[10] + v[9]*v[11] + v[10]*v[11]
	c5 = v[12]*v[13] + v[12]*v[14] + v[13]*v[14]
	c6 = v[15]
		
	c21 = c1 + c2 + c3
	c22 = c4 + c5
	s21 = s1*s2 + s1*s3 + s2*s3
	s22 = s4*s5 + s4*s6 + s5*s6
	s23 = s1*s4 + s1*s5 + s1*s6
	s24 = s2*s4 + s2*s5 + s2*s6
	s25 = s3*s4 + s3*s5 + s3*s6
	result[1] = c21 + c22 + s21 + s22 + s23 + s24 + s25


	c31 = c1*c2 + c1*c3 + c2*c3
	c32 = c1*c4 + c1*c5 + c4*c5
	c33 = c2*c4 + c2*c5
	c34 = c3*c4 + c3*c5

        s31 = s21*s22 + s21*s23 + s22*s23
        s32 = s21*s24 + s21*s25 + s24*s25
        s33 = s22*s24 + s22*s25
        s34 = s23*s24 + s23*s25

        result[2] = (c21 + c22)*(s21 + s22 + s23 + s24 + s24) + c31 + c32 + c33 + c34 + s31 + s32 + s33 + s34

        s35 = (c21 + c22)*(s21 + s22 + s23 + s24 + s24)

        c41 = c31*c32 + c31*c33 + c32*c33
        c42 = c31*c34 + c32*c34 + c33*c34

        s41 = s31*s32 + s31*s33 + s32*s33
        s42 = s31*s34 + s32*s34 + s34*s35
        s43 = s33*s34 + s33*s35 + s32*s35

        result[3] = (c31 + c32 + c33 + c34)*(s31 + s32 + s33 + s34 + s35) + c41 + c42 + s41 + s42 \
                    + s43
	
    else:
        raise Exception('Unsupported length in hamming weight algorithm')
        
    return result


# Utilities

def fill_slots_with_elem(x, nslots):
    v = zero
    for i in range(nslots):
        v = (v << 1) + x
    return v

def fill_slots_with_list(elems, nslots):
    if len(elems) != nslots:
        raise Exception('Number of slots is not equal to number of elements')
    v = zero
    n = nslots - 1
    while n >= 0:
        v >>= 1
        v = v + elems[n]
        n -= 1
    return v


def create_matrix(dims, init_elem=0):
    if len(dims)== 1 :
        return [init_elem] * dims[0]
    M = []
    for i in range(dims[0]):
        M.append(create_matrix(dims[1:], init_elem))
    return M

def transpose(M):
    nrows = len(M)
    ncols = len(M[0])

    Mt = create_matrix([ncols, nrows])
    for i in range(ncols):
        for j in range(nrows):
            Mt[i][j] = M[j][i]
    return Mt

def mul_vect(v1, v2):
    return map(lambda (x, y): x * y, zip(v1, v2))

def sum_vect(v1, v2):
    return map(lambda (x, y): x + y, zip(v1, v2))

def to_constant(n, nbits):
    nbin = [scdf.Constant(0)] * nbits
    i = 0
    while i < nbits and n != 0:
        nbin[i] = scdf.Constant(n & 1)
        n >>= 1
        i += 1
    return nbin

def to_bin(n, nbits):
    nbin = [0] * nbits
    i = 0
    while i < nbits and n != 0:
        nbin[i] = n & 1
        n >>= 1
        i += 1
    return nbin
