import random

def order_crossover(p1, p2):
    size = len(p1)
    a, b = sorted(random.sample(range(size), 2))

    child = [None] * size
    child[a:b] = p1[a:b]

    fill = [x for x in p2 if x not in child]
    ptr = 0
    for i in range(size):
        if child[i] is None:
            child[i] = fill[ptr]
            ptr += 1

    return child

def pmx_crossover(p1, p2):
    size = len(p1)
    c1 = [None] * size

    a, b = sorted(random.sample(range(size), 2))

    # Copy segment
    c1[a:b] = p1[a:b]

    # Mapping
    for i in range(a, b):
        if p2[i] not in c1:
            pos = i
            val = p2[i]
            while True:
                pos = p1.index(val)
                if c1[pos] is None:
                    c1[pos] = p2[i]
                    break
                val = p2[pos]

    # Fill remaining
    for i in range(size):
        if c1[i] is None:
            c1[i] = p2[i]

    return c1
