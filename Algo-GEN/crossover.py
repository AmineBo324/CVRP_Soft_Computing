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

    # 1) copy segment from parent 1
    c1[a:b] = p1[a:b]

    # 2) mapping
    for i in range(a, b):
        if p2[i] not in c1:
            val = p2[i]
            pos = i

            while True:
                mapped = p1[pos]
                pos = p2.index(mapped)

                if c1[pos] is None:
                    c1[pos] = val
                    break

    # 3) fill remaining positions
    for i in range(size):
        if c1[i] is None:
            c1[i] = p2[i]

    return c1

