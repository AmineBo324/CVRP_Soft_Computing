# main.py
import time
import matplotlib.pyplot as plt
import json
import sys
import os

# --------------------------------
# Allow imports from project root
# --------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reader import read_cvrp_instance
from src.cost import build_distance_matrix, solution_cost
from src.feasibility import is_solution_feasible
from ga import genetic_algorithm, decode, local_search_solution

# --------------------------------
# Import operators
# --------------------------------
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

# --------------------------------
# Load instance
# --------------------------------
INSTANCE_PATH = "../instances/A/A-n32-k5.vrp"
instance = read_cvrp_instance(INSTANCE_PATH)

# Precompute distances (IMPORTANT)
dist = build_distance_matrix(instance["coords"])

print(f"\nInstance loaded: {instance['name']}")
print(f"Customers: {len(instance['customers'])}, Capacity: {instance['capacity']}")
if instance["optimal"]:
    print(f"Known optimal: {instance['optimal']}")

# --------------------------------
# Define experiments
# --------------------------------
selection_methods = [
    ("Tournament", tournament_selection),
    ("Roulette", roulette_wheel_selection),
    ("Rank", rank_selection),
    ("Uniform", lambda pop, fit: uniform_selection(pop, len(pop))),
    ("Deterministic", lambda pop, fit: deterministic_selection(pop, fit, len(pop))),
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

# Generate all combinations
experiments = []
for sel_name, sel_func in selection_methods:
    for cross_name, cross_func in crossover_methods:
        for mut_name, mut_func in mutation_methods:
            name = f"{sel_name} + {cross_name} + {mut_name}"
            experiments.append((name, sel_func, cross_func, mut_func))

print(f"\nTotal experiments: {len(experiments)}")

RUNS = 10

results = {}
best_overall = None
all_results = []

# --------------------------------
# Run experiments
# --------------------------------
for idx, (name, sel, cross, mut) in enumerate(experiments, 1):
    print(f"\n[{idx}/{len(experiments)}] Running: {name}")

    best_cost_combo = float("inf")
    best_solution_combo = None
    best_history_combo = None
    best_time_combo = None
    all_costs = []

    for run in range(RUNS):
        seed = 100 + run
        print(f"  Run {run+1}/{RUNS} ...")

        best_chrom, best_cost, history, exec_time = genetic_algorithm(
        instance,
        dist,
        selection=rank_selection,
        crossover=order_crossover,
        mutation=swap_mutation,
        pop_size=120,
        generations=600,
        px=0.9
)


        # Decode + final local search
        sol = decode(best_chrom, instance)
        sol = local_search_solution(sol, dist)
        cost = solution_cost(sol, dist)

        feasible = is_solution_feasible(
            sol,
            demands=instance["demands"],
            capacity=instance["capacity"],
            depot=instance["depot"]
        )

        all_costs.append(cost)

        if feasible and cost < best_cost_combo:
            best_cost_combo = cost
            best_solution_combo = sol
            best_history_combo = history
            best_time_combo = exec_time

    results[name] = best_history_combo if best_history_combo else []

    output = {
        "instance": instance["name"],
        "method": name,
        "best_cost_best_run": round(best_cost_combo, 2),
        "avg_best_cost_over_runs": round(sum(all_costs) / len(all_costs), 2),
        "execution_time_best_run": round(best_time_combo if best_time_combo else 0.0, 2)
    }

    print("\nResult for this experiment:")
    print(json.dumps(output, indent=2))

    all_results.append(output)

    if best_overall is None or best_cost_combo < best_overall["best_cost_best_run"]:
        best_overall = output
        with open("best_solution.txt", "w") as f:
            f.write(str(best_solution_combo))

# --------------------------------
# Save results
# --------------------------------
with open("all_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

if best_overall:
    with open("best_result.json", "w") as f:
        json.dump(best_overall, f, indent=2)

# --------------------------------
# Plot convergence
# --------------------------------
print("\nPlotting convergence curves...")
for name, hist in results.items():
    if hist:
        plt.plot(hist, label=name, alpha=0.7)

plt.xlabel("Generation")
plt.ylabel("Best Cost")
plt.title(f"GA Convergence Comparison ({instance['name']})")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig("convergence_plot.png", dpi=150, bbox_inches='tight')
print("Saved: convergence_plot.png")
plt.show()

# --------------------------------
# Print best combination
# --------------------------------
if best_overall:
    print("\nBest overall combination:")
    print(json.dumps(best_overall, indent=2))
