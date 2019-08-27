from base import *

def ripple_add(a, b):
    if len(a) != len(b):
        raise 'Unequal lengths'
    n = len(a)
    if n is 0:
        raise 'Length is zero'
    s, c = half_adder(a[0], b[0])
    res = [s]
    for i in range(1, n):
        s, c = full_adder(a[i], b[i], c)
        res.append(s)
    res.append(c)
    return res
