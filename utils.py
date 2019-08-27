def to_bin(n, nbits):
    nbin = [0] * nbits
    i = 0
    while i < nbits and n != 0:
        nbin[i] = n & 1
        n >>= 1
        i += 1
    return nbin

def from_bin(bits):
    powers_of_2 = 1
    n = 0
    for b in bits:
        n += b * powers_of_2
        powers_of_2 *= 2
    return int(n)

def is_power_of_2(n):
    if n == 0:
        return False

    while n & 1 == 0:
        n >>= 1

    return n == 1
