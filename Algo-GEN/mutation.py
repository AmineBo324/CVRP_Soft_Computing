import random
def swap_mutation(chrom):
    c = chrom[:]
    i, j = random.sample(range(len(c)), 2)
    c[i], c[j] = c[j], c[i]
    return c


