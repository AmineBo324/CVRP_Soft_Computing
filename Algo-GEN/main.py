import time
import matplotlib.pyplot as plt
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.reader import read_cvrp_instance   
from src.cost import solution_cost
from src.feasibility import is_solution_feasible
from ga import genetic_algorithm, decode

# -----------------------------
# IMPORT YOUR OPERATORS
# -----------------------------
from selection import (
    tournament_selection,
    roulette_wheel_selection,
    rank_selection,
    uniform_selection,
    deterministic_selection,
    remainder_selection
)
from crossover import order_crossover, pmx_crossover
from mutation import swap_mutation, mutation_inversion

# -----------------------------
# Load instance
# -----------------------------
instance = read_cvrp_instance("../instances/A/A-n32-k5.vrp")
# Wrappers pour les sélections qui attendent num_select
def deterministic_sel_wrapper(population, fitnesses):
    return deterministic_selection(population, fitnesses, num_select=len(population))

def uniform_sel_wrapper(population, fitnesses):
    return uniform_selection(population, num_select=len(population))

# -----------------------------
# Define experiments
# -----------------------------
selection_methods = [
    ("Tournament", tournament_selection),
    ("Roulette", roulette_wheel_selection),
    ("Rank", rank_selection),
    ("Uniform", uniform_sel_wrapper),
    ("Deterministic", deterministic_sel_wrapper),
    ("Remainder", remainder_selection)
]

crossover_methods = [
    ("OX", order_crossover),
    ("PMX", pmx_crossover),
]

mutation_methods = [
    ("Swap", swap_mutation),
    ("Inversion", mutation_inversion),
]

# Générer toutes les combinaisons automatiquement
experiments = []
for sel_name, sel_func in selection_methods:
    for cross_name, cross_func in crossover_methods:
        for mut_name, mut_func in mutation_methods:
            name = f"{sel_name} + {cross_name} + {mut_name}"
            experiments.append((name, sel_func, cross_func, mut_func))

print(f"Total experiments: {len(experiments)}")


results = {}  # for plotting
best_overall = None  # store best combination
best_json = None

# -----------------------------
# Run all experiments
# -----------------------------
for name, sel, cross, mut in experiments:
    print(f"Running: {name}")
    start_time = time.time()

    # Run GA
    best_chrom, best_cost, history, _ = genetic_algorithm(
        instance,
        selection=sel,
        crossover=cross,
        mutation=mut,
        pop_size=80,
        generations=200
    )

    exec_time = time.time() - start_time

    # Decode chromosome to routes
    best_solution = decode(best_chrom, instance)

    # Check feasibility
    feasible = is_solution_feasible(
        best_solution,
        demands=instance["demands"],
        capacity=instance["capacity"],
        depot=instance["depot"]
    )

    # Store history for plotting
    results[name] = history

    # Prepare JSON output for this experiment
    output = {
        "instance": instance["name"],
        "method": name,
        "best_cost": round(best_cost, 2),
        "execution_time": round(exec_time, 2),
        "feasible": feasible
    }

    # Track overall best
    if feasible and (best_overall is None or best_cost < best_overall["best_cost"]):
        best_overall = output

    print(json.dumps(output, indent=2))

# -----------------------------
# Plot convergence
# -----------------------------
for name, hist in results.items():
    plt.plot(hist, label=name)

plt.xlabel("Generation")
plt.ylabel("Best Cost")
plt.title(f"GA Convergence Comparison ({instance['name']})")
plt.legend()
plt.grid(True)
plt.show()

# -----------------------------
# Output best combination in JSON
# -----------------------------
if best_overall:
    print("\nBest overall combination:")
    print(json.dumps(best_overall, indent=2))
    # Save to file
    with open("best_result.json", "w") as f:
        json.dump(best_overall, f, indent=2)
