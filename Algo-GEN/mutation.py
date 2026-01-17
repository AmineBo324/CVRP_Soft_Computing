import random
def swap_mutation(chrom):
    c = chrom[:]
    i, j = random.sample(range(len(c)), 2)
    c[i], c[j] = c[j], c[i]
    return c

def mutation_inversion(chrom):
    """
    Inversion mutation: Select a random subsequence and reverse it.
    """
    c = chrom[:]
    start, end = sorted(random.sample(range(len(c)), 2))
    c[start:end+1] = c[start:end+1][::-1]
    return c