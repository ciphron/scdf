from base import *
import arith
from math import log
import utils

def hamming_weight_add(v):
    n = len(v)
    if not utils.is_power_of_2(n):
        raise 'Length of vector is not a power of 2'
    elems = map(lambda x: [x], v)
    while n >= 2:
        n /= 2
        for i in range(n):
            elems[i] = arith.ripple_add(elems[2*i], elems[2*i + 1])
    w = elems[0]

    return w

# This algorithm builds upon and generalizes an approach by
# Cetin, Doroz, Sunar and Savas and handles vectors of any length
def hamming_weight_direct(v):
    c = v
    result_len = int(log(len(v), 2)) + 1
    result = [zero] * result_len
    for i in range(result_len):
        s = []
        n = len(c)
        rem = n % 3
        left_over = c[-rem:]
        for j in range(0, n - rem, 3):
              s.append(c[j] + c[j + 1] + c[j + 2])
        if rem != 0:
            s.append(sum(left_over, zero))

        result[i] = sum(s, zero)
        
        next_c = []

        for j in range(0, n - rem, 3):
            next_c.append(c[j]*c[j + 1] + c[j]*c[j + 2] + c[j + 1]*c[j + 2])
        if rem == 2:
            next_c.append(c[-1]*c[-2])
        for j in range(len(s)):
            t = zero
            for k in range(j + 1, len(s)):
                t += s[j]*s[k]
            next_c.append(t)

        c = next_c
    
    return result 


hamming_weight = hamming_weight_direct
