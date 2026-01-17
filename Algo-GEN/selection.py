import random

def tournament_selection(population, fitnesses, k=3):
    selected = random.sample(list(zip(population, fitnesses)), k)
    return max(selected, key=lambda x: x[1])[0]


def roulette_wheel_selection(population, fitnesses):
    total = sum(fitnesses)
    pick = random.uniform(0, total)
    current = 0
    for chrom, fit in zip(population, fitnesses):
        current += fit
        if current >= pick:
            return chrom

def deterministic_selection(population, fitnesses, num_select):
    """
    Deterministic selection: Select the top num_select individuals based on fitness (highest first).
    """
    sorted_pop = sorted(zip(population, fitnesses), key=lambda x: x[1], reverse=True)
    return [ind for ind, fit in sorted_pop[:num_select]]

def uniform_selection(population, num_select):
    """
    Uniform selection: Randomly select individuals uniformly, ignoring fitness.
    """
    return random.sample(population, num_select)

def rank_selection(population, fitnesses):
    """
    Rank-based selection: Assign probabilities linearly based on rank (best has highest prob).
    """
    sorted_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
    ranks = [0] * len(population)
    for rank, idx in enumerate(sorted_indices):
        ranks[idx] = len(population) - rank  # Best rank = len(pop), worst = 1

    total = sum(ranks)
    pick = random.uniform(0, total)
    current = 0
    for i, rank in enumerate(ranks):
        current += rank
        if current >= pick:
            return population[i]

def remainder_selection(population, fitnesses):
    """
    Stochastic remainder selection: Proportional selection with integer and fractional parts.
    First, select floor(expected) copies deterministically, then probabilistic for remainders.
    Assumes we select the entire population size.
    """
    pop_size = len(population)
    total_fit = sum(fitnesses)
    expected = [pop_size * (fit / total_fit) for fit in fitnesses]

    new_pop = []
    remainders = []

    for i, exp in enumerate(expected):
        integer_part = int(exp)
        fractional_part = exp - integer_part
        new_pop.extend([population[i]] * integer_part)
        if fractional_part > 0:
            remainders.append((i, fractional_part))

    # Probabilistic selection for remainders
    remainders.sort(key=lambda x: x[1], reverse=True)
    needed = pop_size - len(new_pop)
    for i in range(needed):
        if remainders:
            idx, _ = remainders[i % len(remainders)]
            new_pop.append(population[idx])

    return new_pop