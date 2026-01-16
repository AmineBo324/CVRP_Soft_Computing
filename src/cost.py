def euclidean_distance(a, b):
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5


def solution_cost(solution, coords):
    total_cost = 0.0

    for route in solution:
        for i in range(len(route) - 1):
            a = coords[route[i]]
            b = coords[route[i + 1]]
            total_cost += euclidean_distance(a, b)

    return total_cost
