def is_solution_feasible(solution, demands, capacity, depot):
    served_clients = set()

    for route in solution:
        # Check depot
        if route[0] != depot or route[-1] != depot:
            return False

        load = 0
        for node in route[1:-1]:
            if node in served_clients:
                return False

            served_clients.add(node)
            load += demands[node]

        if load > capacity:
            return False

    all_clients = set(demands.keys()) - {depot}
    return served_clients == all_clients
