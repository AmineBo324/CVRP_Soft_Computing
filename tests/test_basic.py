from src.reader import read_cvrp_instance
from src.solution_reader import read_solution_file
from src.feasibility import is_solution_feasible
from src.cost import solution_cost

# Load instance
instance = read_cvrp_instance("instances/B/B-n31-k5.vrp")

# Load optimal solution
solution = read_solution_file("instances/B/B-n31-k5.sol")

# Feasibility check
feasible = is_solution_feasible(
    solution,
    instance["demands"],
    instance["capacity"],
    instance["depot"]
)

print("Feasible:", feasible)

# Cost computation
if feasible:
    cost = solution_cost(solution, instance["coords"])
    print("Computed cost:", cost)
    print("Known optimum:", instance["optimal"])
