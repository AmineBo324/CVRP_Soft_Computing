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
    pop_size=150,
    generations=800,
    px=0.9,
    pm=0.2
):
    customers = instance["customers"]
    population = [random.sample(customers, len(customers)) for _ in range(pop_size)]
    best_cost = float("inf")
    history = []

    start_time = time.time()

    elite_size = max(1, pop_size // 20)

    best_chrom = None
    best_cost = float("inf")

    for gen in range(generations):
        fitnesses = []
        costs = []

        # ---- FITNESS ----
        for chrom in population:
            cost = solution_cost(decode(chrom, instance), instance["coords"])
            costs.append(cost)
            fitnesses.append(1 / (cost + 1e-6))

            if cost < best_cost:
                best_cost = cost
                best_chrom = chrom[:]

        # ---- ELITISM ----
        ranked = sorted(
            zip(population, costs),
            key=lambda x: x[1]
        )
        elites = [c[:] for c, _ in ranked[:elite_size]]

        new_population = elites[:]

        # ---- REPRODUCTION ----
        while len(new_population) < pop_size:
            p1 = selection(population, fitnesses)[:]
            p2 = selection(population, fitnesses)[:]

            child = crossover(p1, p2) if random.random() < px else p1[:]

            if random.random() < pm:
                child = mutation(child[:])

            if not is_valid_chromosome(child, customers):
                child = repair_chromosome(child, customers)

            new_population.append(child)

        population = new_population

        gen_best = min(costs)
        history.append(gen_best)



    exec_time = time.time() - start_time
    return best_chrom, best_cost, history, exec_time