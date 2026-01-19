# src/cost.py
import math

def euclidean_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def build_distance_matrix(coords):
    dist = {}
    nodes = list(coords.keys())
    for i in nodes:
        for j in nodes:
            dist[(i, j)] = euclidean_distance(coords[i], coords[j])
    return dist

def solution_cost(solution, dist):
    total = 0.0
    for route in solution:
        for i in range(len(route) - 1):
            total += dist[(route[i], route[i + 1])]
    return total
