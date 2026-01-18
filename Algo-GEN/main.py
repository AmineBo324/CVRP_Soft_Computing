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

# Load instance
instance = read_cvrp_instance("../instances/A/A-n32-k5.vrp")

# Wrappers for selections that expect num_select
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

# Generate all combinations
experiments = []
for sel_name, sel_func in selection_methods:
    for cross_name, cross_func in crossover_methods:
        for mut_name, mut_func in mutation_methods:
            name = f"{sel_name} + {cross_name} + {mut_name}"
            experiments.append((name, sel_func, cross_func, mut_func))

print(f"Total experiments: {len(experiments)}\n")

results = {}
best_overall = None
best_json = None
all_results = []   # ✅ This will store ALL 24 results

# -----------------------------
# Run all experiments
# -----------------------------
for idx, (name, sel, cross, mut) in enumerate(experiments, 1):
    print(f"[{idx}/{len(experiments)}] Running: {name}")
    start_time = time.time()

    try:
        best_chrom, best_cost, history, _ = genetic_algorithm(
            instance,
            selection=sel,
            crossover=cross,
            mutation=mut,
            pop_size=50,
            generations=200
        )

        exec_time = time.time() - start_time

        best_solution = decode(best_chrom, instance)

        feasible = is_solution_feasible(
            best_solution,
            demands=instance["demands"],
            capacity=instance["capacity"],
            depot=instance["depot"]
        )

        results[name] = history

        output = {
            "instance": instance["name"],
            "method": name,
            "best_cost": round(best_cost, 2),
            "execution_time": round(exec_time, 2),
            "feasible": feasible
        }

        # ✅ KEEP collecting all experiment results
        all_results.append(output)

        if feasible and (best_overall is None or best_cost < best_overall["best_cost"]):
            best_overall = output
            best_json = output.copy()

        print(json.dumps(output, indent=2))

    except Exception as e:
        output = {
            "instance": instance["name"],
            "method": name,
            "best_cost": float('inf'),
            "execution_time": round(time.time() - start_time, 2),
            "feasible": False
        }
        all_results.append(output)
        print(json.dumps(output, indent=2))

# -----------------------------
# SAVE RESULTS (FIXED)
# -----------------------------
print("\n" + "=" * 70)
print("SAVING RESULTS TO all_results.json")
print("=" * 70)

all_results_file = "all_results.json"

# Load existing results safely
existing_results = []
if os.path.exists(all_results_file):
    with open(all_results_file, "r") as f:
        try:
            existing_results = json.load(f)
            if not isinstance(existing_results, list):
                existing_results = [existing_results]
        except json.JSONDecodeError:
            existing_results = []

# ✅ MERGE instead of overwrite
existing_results.extend(all_results)

with open(all_results_file, "w") as f:
    json.dump(existing_results, f, indent=2)

print(f"✅ Saved {len(all_results)} new results "
      f"(Total: {len(existing_results)})")

# Compatibility file (last run only)
with open("result.json", "w") as f:
    json.dump(all_results[-1], f, indent=2)

# Best result
if best_json:
    with open("best_result.json", "w") as f:
        json.dump(best_json, f, indent=2)
    print("✅ Saved: best_result.json")

# Print best combination
if best_overall:
    print("\nBest overall combination:")
    print(json.dumps(best_overall, indent=2))

# -----------------------------
# Plot convergence
# -----------------------------
print("\n" + "=" * 70)
print("GENERATING CONVERGENCE PLOT")
print("=" * 70)

for name, hist in results.items():
    plt.plot(hist, label=name, alpha=0.7)

plt.xlabel("Generation")
plt.ylabel("Best Cost")
plt.title(f"GA Convergence Comparison ({instance['name']})")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig("convergence_plot.png", dpi=150, bbox_inches='tight')
print("✅ Saved: convergence_plot.png")
plt.show()
