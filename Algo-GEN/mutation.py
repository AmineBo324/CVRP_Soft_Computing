import random
def swap_mutation(chrom):
    c = chrom[:]
    i, j = random.sample(range(len(c)), 2)
    c[i], c[j] = c[j], c[i]
    return c

def order_crossover(p1, p2):
    # Standard OX: only customers
    size = len(p1)
    start, end = sorted(random.sample(range(size), 2))
    child = [None] * size
    child[start:end] = p1[start:end]

    ptr = 0
    for gene in p2:
        if gene not in child:
            while child[ptr] is not None:
                ptr += 1
            child[ptr] = gene
    return child
