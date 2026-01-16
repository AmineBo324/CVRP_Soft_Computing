def read_solution_file(sol_path, depot=1):
    solution = []

    with open(sol_path, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("Route"):
                nodes = list(map(int, line.split(":")[1].split()))
                nodes = [n for n in nodes if n != depot]
                route = [depot] + nodes + [depot]
                solution.append(route)

    return solution
