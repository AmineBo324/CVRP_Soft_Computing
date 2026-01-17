import time
import matplotlib.pyplot as plt
import json
from src.reader import read_cvrp_instance
from src.cost import solution_cost
from src.feasibility import is_solution_feasible
from ga import genetic_algorithm, decode

# -----------------------------
# IMPORT YOUR OPERATORS
# -----------------------------
from selection import tournament_selection, roulette_wheel_selection
from crossover import order_crossover, pmx_crossover
from mutation import swap_mutation, mutation_inversion

# -----------------------------
# Load instance
# -----------------------------
instance = read_cvrp_instance("../instances/A/A-n32-k5.vrp")

# -----------------------------
# Define experiments
# -----------------------------
experiments = [
    ("Tournament + OX + Swap", tournament_selection, order_crossover, swap_mutation),
    ("Tournament + OX + Inversion", tournament_selection, order_crossover, mutation_inversion),
    ("Roulette + OX + Swap", roulette_wheel_selection, order_crossover, swap_mutation),
    ("Roulette + PMX + Inversion", roulette_wheel_selection, pmx_crossover, mutation_inversion)
]

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
        pop_size=50,
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
