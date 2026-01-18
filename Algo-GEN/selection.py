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


"""
def deterministic_selection(population, fitnesses, num_select):
    
    #Deterministic selection: Select the top num_select individuals based on fitness (highest first).

    sorted_pop = sorted(zip(population, fitnesses), key=lambda x: x[1], reverse=True)
    return [ind for ind, fit in sorted_pop[:num_select]]
"""

"""
FIXED DETERMINISTIC SELECTION
Replace the deterministic_selection function in your selection.py file with this one.
The previous version returned a list instead of individual chromosomes.
"""

def deterministic_selection(population, fitnesses, num_select=None):
    """
    Deterministic Selection: Return the best individual based on fitness.
    This operator always selects the individual with the highest fitness.
    
    Args:
        population: List of chromosomes
        fitnesses: List of fitness values (higher is better)
        num_select: Number of individuals to select (kept for compatibility)
    
    Returns:
        Single best individual from population
    """
    if not population or not fitnesses:
        return None
    
    # Find the index of the best individual
    best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    
    # Return the best chromosome (single individual, not list)
    return population[best_idx]

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

    import random

    N = len(population)
    total_fit = sum(fitnesses)

    if total_fit == 0:
        return random.choice(population)


    probabilities = [f / total_fit for f in fitnesses]
    E_values = [N * p for p in probabilities]


    selected_indices = []
    for i, E in enumerate(E_values):
        count = int(E)  # Ent(Ei)
        selected_indices.extend([i] * count)


    remainders = [E - int(E) for E in E_values]
    total_remainder = sum(remainders)


    while len(selected_indices) < N:
        if total_remainder > 0:
            # Sélection par roulette sur les restes
            rand = random.uniform(0, total_remainder)
            cumulative = 0
            for i, remainder in enumerate(remainders):
                cumulative += remainder
                if rand <= cumulative:
                    selected_indices.append(i)
                    break
        else:

            selected_indices.append(random.randint(0, N - 1))


    chosen_index = random.choice(selected_indices)
    return population[chosen_index]

