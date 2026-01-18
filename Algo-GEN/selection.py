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
    sorted_pop = sorted(zip(population, fitnesses), key=lambda x: x[1], reverse=True)
    return [ind for ind, fit in sorted_pop[:num_select]]

def uniform_selection(population, fitnesses=None):
    return random.choice(population)

def rank_selection(population, fitnesses):

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

