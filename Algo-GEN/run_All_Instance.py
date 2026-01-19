import time
import matplotlib.pyplot as plt
import json
import sys
import os
from pathlib import Path
import numpy as np
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reader import read_cvrp_instance
from src.cost import solution_cost
from src.feasibility import is_solution_feasible
from ga import genetic_algorithm, decode

# Import operators
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

# -----------------------------
# Configuration
# -----------------------------
INSTANCE_FOLDERS = ["../instances/A", "../instances/B"]
OUTPUT_DIR = "multi_instance_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)


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
            name = f"{sel_name}+{cross_name}+{mut_name}"
            experiments.append((name, sel_func, cross_func, mut_func))


# -----------------------------
# Collect all instance files
# -----------------------------
def get_instance_files(folders):
    """Collect all .vrp files from specified folders"""
    files = []
    for folder in folders:
        folder_path = Path(folder)
        if folder_path.exists():
            vrp_files = sorted(folder_path.glob("*.vrp"))
            files.extend(vrp_files)
    return files


instance_files = get_instance_files(INSTANCE_FOLDERS)
print(f"Found {len(instance_files)} instances to test")
print(f"Testing {len(experiments)} combinations per instance")
print(f"Total runs: {len(instance_files) * len(experiments)}\n")

# -----------------------------
# Data structures for results
# -----------------------------
all_results = []
combination_stats = defaultdict(lambda: {
    'total_cost': 0,
    'total_time': 0,
    'feasible_count': 0,
    'instance_count': 0,
    'costs': [],
    'instance_results': []
})

# -----------------------------
# Main testing loop
# -----------------------------
print("=" * 80)
print("STARTING MULTI-INSTANCE TESTING")
print("=" * 80)

for instance_idx, instance_file in enumerate(instance_files, 1):
    print(f"\n{'=' * 80}")
    print(f"INSTANCE {instance_idx}/{len(instance_files)}: {instance_file.name}")
    print(f"{'=' * 80}")

    try:
        instance = read_cvrp_instance(str(instance_file))
    except Exception as e:
        print(f"❌ Failed to load instance: {e}")
        continue

    instance_results = []

    for exp_idx, (name, sel, cross, mut) in enumerate(experiments, 1):
        print(f"  [{exp_idx}/{len(experiments)}] {name}...", end=" ", flush=True)

        start_time = time.time()

        try:
            best_chrom, best_cost, history, _ = genetic_algorithm(
                instance,
                selection=sel,
                crossover=cross,
                mutation=mut,
                pop_size=80,
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

            result = {
                "instance": instance["name"],
                "instance_file": instance_file.name,
                "method": name,
                "best_cost": round(best_cost, 2),
                "execution_time": round(exec_time, 2),
                "feasible": feasible
            }

            # Store result
            all_results.append(result)
            instance_results.append(result)

            # Update combination statistics
            combination_stats[name]['instance_count'] += 1
            combination_stats[name]['total_time'] += exec_time
            combination_stats[name]['costs'].append(best_cost)
            combination_stats[name]['instance_results'].append(result)

            if feasible:
                combination_stats[name]['total_cost'] += best_cost
                combination_stats[name]['feasible_count'] += 1

            status = "✓" if feasible else "✗"
            print(f"{status} Cost: {best_cost:.2f}, Time: {exec_time:.2f}s")

        except Exception as e:
            exec_time = time.time() - start_time
            result = {
                "instance": instance["name"],
                "instance_file": instance_file.name,
                "method": name,
                "best_cost": float('inf'),
                "execution_time": round(exec_time, 2),
                "feasible": False,
                "error": str(e)
            }
            all_results.append(result)
            instance_results.append(result)
            combination_stats[name]['instance_count'] += 1
            print(f"✗ ERROR: {str(e)[:50]}")

    # Save instance-specific results
    instance_output_file = os.path.join(OUTPUT_DIR, f"{instance_file.stem}_results.json")
    with open(instance_output_file, "w") as f:
        json.dump(instance_results, f, indent=2)

# -----------------------------
# Calculate final rankings
# -----------------------------
print("\n" + "=" * 80)
print("CALCULATING FINAL RANKINGS")
print("=" * 80)

rankings = []
for name, stats in combination_stats.items():
    if stats['feasible_count'] > 0:
        avg_cost = stats['total_cost'] / stats['feasible_count']
        avg_time = stats['total_time'] / stats['instance_count']
        feasibility_rate = stats['feasible_count'] / stats['instance_count']

        rankings.append({
            'method': name,
            'avg_cost': round(avg_cost, 2),
            'avg_time': round(avg_time, 2),
            'feasible_count': stats['feasible_count'],
            'total_instances': stats['instance_count'],
            'feasibility_rate': round(feasibility_rate * 100, 2),
            'min_cost': round(min(stats['costs']), 2),
            'max_cost': round(max(stats['costs']), 2),
            'std_cost': round(np.std(stats['costs']), 2)
        })

# Sort by: feasibility rate (desc), then avg cost (asc)
rankings.sort(key=lambda x: (-x['feasibility_rate'], x['avg_cost']))

# -----------------------------
# Save all results
# -----------------------------
print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

# Save all individual results
with open(os.path.join(OUTPUT_DIR, "all_results.json"), "w") as f:
    json.dump(all_results, f, indent=2)
print(f"✅ Saved: {OUTPUT_DIR}/all_results.json ({len(all_results)} results)")

# Save rankings
with open(os.path.join(OUTPUT_DIR, "rankings.json"), "w") as f:
    json.dump(rankings, f, indent=2)
print(f"✅ Saved: {OUTPUT_DIR}/rankings.json")

# Save best combination details
if rankings:
    best = rankings[0]
    best_method = best['method']
    best_details = {
        'best_combination': best,
        'detailed_results': combination_stats[best_method]['instance_results']
    }

    with open(os.path.join(OUTPUT_DIR, "best_combination.json"), "w") as f:
        json.dump(best_details, f, indent=2)
    print(f"✅ Saved: {OUTPUT_DIR}/best_combination.json")

# -----------------------------
# Print summary
# -----------------------------
print("\n" + "=" * 80)
print("TOP 10 COMBINATIONS")
print("=" * 80)
print(f"{'Rank':<5} {'Method':<30} {'Avg Cost':<12} {'Feasible':<12} {'Avg Time':<10}")
print("-" * 80)

for i, rank in enumerate(rankings[:10], 1):
    feasible_str = f"{rank['feasible_count']}/{rank['total_instances']}"
    print(f"{i:<5} {rank['method']:<30} {rank['avg_cost']:<12.2f} "
          f"{feasible_str:<12} {rank['avg_time']:<10.2f}s")

if rankings:
    print("\n" + "=" * 80)
    print("🏆 BEST COMBINATION")
    print("=" * 80)
    best = rankings[0]
    print(f"Method: {best['method']}")
    print(f"Average Cost: {best['avg_cost']:.2f}")
    print(f"Feasibility Rate: {best['feasibility_rate']:.1f}%")
    print(f"Average Time: {best['avg_time']:.2f}s")
    print(f"Cost Range: {best['min_cost']:.2f} - {best['max_cost']:.2f}")
    print(f"Standard Deviation: {best['std_cost']:.2f}")

# -----------------------------
# Generate visualization
# -----------------------------
print("\n" + "=" * 80)
print("GENERATING VISUALIZATIONS")
print("=" * 80)

# Plot 1: Average cost comparison
plt.figure(figsize=(15, 8))
methods = [r['method'] for r in rankings[:10]]
costs = [r['avg_cost'] for r in rankings[:10]]
colors = ['green' if r['feasibility_rate'] == 100 else 'orange' for r in rankings[:10]]

plt.barh(methods, costs, color=colors)
plt.xlabel('Average Cost')
plt.title('Top 10 Combinations - Average Cost Across All Instances')
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "avg_cost_comparison.png"), dpi=150, bbox_inches='tight')
print(f"✅ Saved: {OUTPUT_DIR}/avg_cost_comparison.png")

# Plot 2: Feasibility rate
plt.figure(figsize=(15, 8))
feasibility_rates = [r['feasibility_rate'] for r in rankings[:10]]
plt.barh(methods, feasibility_rates, color='steelblue')
plt.xlabel('Feasibility Rate (%)')
plt.title('Top 10 Combinations - Feasibility Rate')
plt.xlim(0, 100)
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "feasibility_comparison.png"), dpi=150, bbox_inches='tight')
print(f"✅ Saved: {OUTPUT_DIR}/feasibility_comparison.png")

plt.show()

print("\n" + "=" * 80)
print("✅ TESTING COMPLETE!")
print(f"Results saved to: {OUTPUT_DIR}/")
print("=" * 80)