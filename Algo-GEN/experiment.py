import json
from ga import genetic_algorithm, decode
from selection import tournament_selection
from crossover import order_crossover
from mutation import swap_mutation
from src.cost import solution_cost
from src.reader import read_cvrp_instance
import time
from src.feasibility import is_solution_feasible

# Load instance
instance = read_cvrp_instance("../instances/A/A-n32-k5.vrp")

# Run GA
start_time = time.time()
best_chrom, best_cost, history, exec_time = genetic_algorithm(
    instance,
    selection=tournament_selection,
    crossover=order_crossover,
    mutation=swap_mutation,
    pop_size=50,
    generations=200
)

# Decode the chromosome to routes
best_solution = decode(best_chrom, instance)

# Check feasibility
feasible = is_solution_feasible(
    best_solution,
    demands=instance["demands"],
    capacity=instance["capacity"],
    depot=instance["depot"]
)

# Prepare JSON output
output = {
    "instance": instance["name"],
    "method": "Genetic Algorithm",
    "best_cost": round(solution_cost(best_solution, instance["coords"]), 2),
    "execution_time": round(exec_time, 2),
    "feasible": feasible
}

# Print or save
print(json.dumps(output, indent=2))
with open("result.json", "w") as f:
    json.dump(output, f, indent=2)
