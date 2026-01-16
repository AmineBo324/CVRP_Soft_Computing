import json

def save_result(instance, method, solution, cost, exec_time, feasible, filename):
    result = {
        "instance": instance,
        "method": method,
        "best_solution": solution,
        "best_cost": cost,
        "execution_time": exec_time,
        "feasible": feasible
    }

    with open(filename, "w") as f:
        json.dump(result, f, indent=4)
