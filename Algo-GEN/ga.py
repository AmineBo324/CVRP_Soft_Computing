import random
import time
from selection import *
from crossover import *
from mutation import *
from src.cost import solution_cost

# -----------------------------
# Decode chromosome to routes
# -----------------------------
def decode(chromosome, instance):
    routes = []
    route = [instance["depot"]]
    load = 0

    for c in chromosome:
        if c is None:
            continue  # safety
        demand = instance["demands"][c]
        if load + demand > instance["capacity"]:
            route.append(instance["depot"])
            routes.append(route)
            route = [instance["depot"]]
            load = 0

        route.append(c)
        load += demand

    route.append(instance["depot"])
    routes.append(route)
    return routes

# -----------------------------
# Chromosome validation and repair
# -----------------------------
def is_valid_chromosome(chrom, customers):
    """
    Checks if chromosome is valid: complete permutation, no None.
    """
    return (
        None not in chrom
        and len(chrom) == len(customers)
        and set(chrom) == set(customers)
    )

def repair_chromosome(chrom, customers):
    """
    Replaces invalid chromosome with a random permutation.
    """
    return random.sample(customers, len(customers))

# -----------------------------
# Genetic Algorithm
# -----------------------------
def genetic_algorithm(
    instance,
    selection,
    crossover,
    mutation,
    pop_size=100,
    generations=300,
    px=0.9,
    pm=0.2
):
    customers = instance["customers"]
    population = [random.sample(customers, len(customers)) for _ in range(pop_size)]
    best_cost = float("inf")
    history = []

    start_time = time.time()

    for gen in range(generations):
        # Compute fitness safely
        fitnesses = []
        for chrom in population:
            # Compute cost
            cost = solution_cost(decode(chrom, instance), instance["coords"])

            fitnesses.append(1 / (cost + 1e-6))

            if cost < best_cost:
                best_cost = cost
                best_chrom = chrom[:]

        new_population = []

        while len(new_population) < pop_size:
            # Copy parents to avoid in-place modification
            p1 = selection(population, fitnesses)[:]
            p2 = selection(population, fitnesses)[:]

            # Crossover
            child = crossover(p1, p2) if random.random() < px else p1[:]

            # Mutation
            if random.random() < pm:
                child = mutation(child[:])

            # Repair invalid chromosome
            if not is_valid_chromosome(child, customers):
                child = repair_chromosome(child, customers)

            new_population.append(child)


        population = new_population

        # Track best cost for this generation
        gen_best = min(
            solution_cost(decode(c, instance), instance["coords"])
            for c in population
        )
        best_cost = min(best_cost, gen_best)
        history.append(best_cost)


    exec_time = time.time() - start_time
    return best_chrom, best_cost, history, exec_time
