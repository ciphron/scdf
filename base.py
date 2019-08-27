import scdf

zero = scdf.Constant(0)
one = scdf.Constant(1)

def eq1(x, y):
    return x + y + one

def lor(x, y):
    return x*y + x + y

def eq(xs, ys):
    is_eq = one
    for i in range(len(xs)):
        is_eq *= eq1(xs[i], ys[i])
    return is_eq

def lnot(x):
    return x + one

def lt1(x, y):
    return lnot(x) * y

def lt(xs, ys):
    is_eq = one
    is_lt = lt1(xs[-1], ys[-1])
    n = len(xs) - 2
    while n >= 0:
        is_eq *= eq1(xs[n + 1], ys[n + 1])
        is_lt += is_eq * lt1(xs[n], ys[n])
        n -= 1
    return is_lt

def mux1(sel, alt0, alt1):
    return lnot(sel)*alt0 + sel*alt1

def mux(sel, alt0, alt1):
    t = []
    for i in range(len(alt0)):
        t.append(mux1(sel, alt0[i], alt1[i]))
    return t

def half_adder(a, b):
    s = a + b
    c = a * b
    return (s, c)

def full_adder(a, b, c_in):
	s0 = a + b
	s = s0 + c_in
	#c_out = lor(a*b, c_in * s0)
	t1 = c_in * a
	t2 = c_in * b
	t3 = t1 * b
	t4 = t2 * a
	c_out = a*b + t1 + t2 + t3 + t4
	return (s, c_out)
