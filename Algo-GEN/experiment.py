import matplotlib.pyplot as plt
from ga import genetic_algorithm
from selection import *
from crossover import *
from mutation import *
from src.reader import read_cvrp_instance

instance = read_cvrp_instance("../instances/A/A-n32-k5.vrp")

experiments = [
    ("Tournament + OX + Swap",
     tournament_selection, order_crossover, swap_mutation),

    #("Tournament + OX + Inversion",
     #tournament_selection, order_crossover, inversion_mutation),

    ("Roulette + PMX + Swap",
     roulette_wheel_selection, pmx_crossover, swap_mutation)
]

results = {}

for name, sel, cross, mut in experiments:
    best, hist, t = genetic_algorithm(
        instance,
        selection=sel,
        crossover=cross,
        mutation=mut,
        pop_size=100,
        generations=300
    )
    results[name] = hist
    print(f"{name} → Best: {best:.2f} | Time: {t:.2f}s")

for name, hist in results.items():
    plt.plot(hist, label=name)

plt.xlabel("Generation")
plt.ylabel("Best Cost")
plt.title("GA Convergence Comparison")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
