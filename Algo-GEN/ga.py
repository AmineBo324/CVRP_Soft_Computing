# ga.py
import random
import time
from src.cost import solution_cost

# -----------------------------
# Decode chromosome to routes
# -----------------------------
def decode(chromosome, instance):
    routes = []
    route = [instance["depot"]]
    load = 0

    for c in chromosome:
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
# Chromosome validation / repair
# -----------------------------
def is_valid_chromosome(chrom, customers):
    return (
        chrom is not None and
        len(chrom) == len(customers) and
        set(chrom) == set(customers)
    )

def repair_chromosome(customers):
    return random.sample(customers, len(customers))

# -----------------------------
# Local search: 2-opt
# -----------------------------
def _route_cost(route, dist):
    return sum(dist[(route[i], route[i+1])] for i in range(len(route)-1))

def two_opt_route(route, dist):
    if len(route) <= 4:
        return route

    best = route[:]
    best_cost = _route_cost(best, dist)
    improved = True

    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                new = best[:]
                new[i:j] = reversed(best[i:j])
                c = _route_cost(new, dist)
                if c < best_cost:
                    best, best_cost = new, c
                    improved = True
    return best

def local_search_solution(solution, dist):
    return [two_opt_route(r, dist) for r in solution]

# -----------------------------
# Genetic Algorithm
# -----------------------------
def genetic_algorithm(
    instance,
    dist,
    selection,
    crossover,
    mutation,
    pop_size=80,
    generations=300,
    px=0.9,
    pm=0.25
):
    customers = instance["customers"]
    population = [random.sample(customers, len(customers)) for _ in range(pop_size)]

    elite_size = max(1, pop_size // 20)
    best_cost = float("inf")
    best_chrom = None
    history = []

    start_time = time.time()

    for gen in range(generations):
        fitnesses, costs = [], []

        # ---------- Evaluation ----------
        for chrom in population:
            sol = decode(chrom, instance)

            # ✅ Local search (clé pour ~797)
            sol = local_search_solution(sol, dist)

            cost = solution_cost(sol, dist)
            costs.append(cost)
            fitnesses.append(1.0 / (cost + 1e-9))

            if cost < best_cost:
                best_cost = cost
                best_chrom = chrom[:]

        # ---------- Elitism ----------
        ranked = sorted(zip(population, costs), key=lambda x: x[1])
        elites = [c[:] for c, _ in ranked[:elite_size]]
        new_population = elites[:]

        # ---------- Reproduction ----------
        while len(new_population) < pop_size:
            p1 = selection(population, fitnesses)[:]
            p2 = selection(population, fitnesses)[:]

            child = crossover(p1, p2) if random.random() < px else p1[:]

            if random.random() < pm:
                child = mutation(child)

            # ✅ sécurité ضد PMX
            if not is_valid_chromosome(child, customers):
                child = repair_chromosome(customers)

            new_population.append(child)

        population = new_population
        history.append(min(costs))

    return best_chrom, best_cost, history, time.time() - start_time
