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
from src.cost import build_distance_matrix, solution_cost
from src.feasibility import is_solution_feasible
from ga import genetic_algorithm, decode, local_search_solution

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

# ================================
# CONFIGURATION
# ================================
INSTANCE_FOLDERS = ["../instances/A", "../instances/B"]
OUTPUT_DIR = "multi_instance_results"
RUNS_PER_COMBINATION = 10  # Multiple runs per combination for statistical validity
SEED_START = 100


# ================================
# Helper Functions
# ================================
def get_instance_files(folders):
    """Collect all .vrp files from specified folders"""
    files = []
    for folder in folders:
        folder_path = Path(folder)
        if folder_path.exists():
            vrp_files = sorted(folder_path.glob("*.vrp"))
            files.extend(vrp_files)
        else:
            print(f"⚠️  Warning: Folder not found: {folder}")
    return files


def get_experiments():
    """Generate all experiment combinations"""
    selection_methods = [
        ("Tournament", tournament_selection),
        ("Roulette", roulette_wheel_selection),
        ("Rank", rank_selection),
        ("Uniform", lambda pop, fit: uniform_selection(pop, len(pop))),
        ("Deterministic", lambda pop, fit: deterministic_selection(pop, fit, len(pop))),
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

    experiments = []
    for sel_name, sel_func in selection_methods:
        for cross_name, cross_func in crossover_methods:
            for mut_name, mut_func in mutation_methods:
                name = f"{sel_name}+{cross_name}+{mut_name}"
                experiments.append((name, sel_func, cross_func, mut_func))

    return experiments


# ================================
# Main Testing Function
# ================================
def run_multi_instance_test():
    """Run comprehensive testing across all instances and combinations"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    experiments = get_experiments()
    instance_files = get_instance_files(INSTANCE_FOLDERS)

    if not instance_files:
        print("❌ No instance files found! Check your folder paths.")
        print(f"   Looking in: {INSTANCE_FOLDERS}")
        return

    print("=" * 80)
    print("MULTI-INSTANCE GA TESTING - OPTIMIZED VERSION")
    print("=" * 80)
    print(f"Instances found: {len(instance_files)}")
    print(f"Combinations to test: {len(experiments)}")
    print(f"Runs per combination: {RUNS_PER_COMBINATION}")
    print(f"Total runs: {len(instance_files) * len(experiments) * RUNS_PER_COMBINATION}")
    print("=" * 80)

    # Data structures
    all_results = []
    combination_stats = defaultdict(lambda: {
        'total_best_cost': 0,
        'total_avg_cost': 0,
        'total_time': 0,
        'feasible_count': 0,
        'instance_count': 0,
        'all_costs': [],
        'instance_results': []
    })

    # ================================
    # Main Testing Loop
    # ================================
    for instance_idx, instance_file in enumerate(instance_files, 1):
        print(f"\n{'=' * 80}")
        print(f"INSTANCE {instance_idx}/{len(instance_files)}: {instance_file.name}")
        print(f"{'=' * 80}")

        try:
            instance = read_cvrp_instance(str(instance_file))
            dist = build_distance_matrix(instance["coords"])

            if instance["optimal"]:
                print(f"Known optimal cost: {instance['optimal']}")

        except Exception as e:
            print(f"❌ Failed to load instance: {e}")
            continue

        instance_results = []

        # Test each combination
        for exp_idx, (name, sel, cross, mut) in enumerate(experiments, 1):
            print(f"  [{exp_idx}/{len(experiments)}] {name}...", end=" ", flush=True)

            best_cost_combo = float("inf")
            best_solution_combo = None
            all_costs = []
            total_time = 0

            # Multiple runs for this combination
            for run in range(RUNS_PER_COMBINATION):
                seed = SEED_START + run
                random.seed(seed)
                np.random.seed(seed)

                start_time = time.time()

                try:
                    best_chrom, best_cost, history, exec_time = genetic_algorithm(
                        instance,
                        dist,
                        selection=sel,
                        crossover=cross,
                        mutation=mut,
                        pop_size=120,
                        generations=600,
                        px=0.9,
                        pm=0.25
                    )

                    # Decode + final local search
                    sol = decode(best_chrom, instance)
                    sol = local_search_solution(sol, dist)
                    cost = solution_cost(sol, dist)

                    feasible = is_solution_feasible(
                        sol,
                        demands=instance["demands"],
                        capacity=instance["capacity"],
                        depot=instance["depot"]
                    )

                    if feasible:
                        all_costs.append(cost)
                        if cost < best_cost_combo:
                            best_cost_combo = cost
                            best_solution_combo = sol

                    total_time += exec_time

                except Exception as e:
                    print(f"\n    ⚠️  Run {run + 1} failed: {str(e)[:50]}")
                    continue

            # Calculate statistics for this combination on this instance
            if all_costs:
                avg_cost = np.mean(all_costs)
                std_cost = np.std(all_costs)
                min_cost = min(all_costs)
                avg_time = total_time / RUNS_PER_COMBINATION

                # Calculate gap from optimal if known
                gap = None
                if instance["optimal"] and instance["optimal"] > 0:
                    gap = ((best_cost_combo - instance["optimal"]) / instance["optimal"]) * 100

                result = {
                    "instance": instance["name"],
                    "instance_file": instance_file.name,
                    "method": name,
                    "best_cost": round(best_cost_combo, 2),
                    "avg_cost": round(avg_cost, 2),
                    "std_cost": round(std_cost, 2),
                    "min_cost": round(min_cost, 2),
                    "avg_time": round(avg_time, 2),
                    "runs": len(all_costs),
                    "feasible": True,
                    "gap_from_optimal": round(gap, 2) if gap is not None else None,
                    "optimal": instance["optimal"]
                }

                # Update combination statistics
                combination_stats[name]['total_best_cost'] += best_cost_combo
                combination_stats[name]['total_avg_cost'] += avg_cost
                combination_stats[name]['total_time'] += avg_time
                combination_stats[name]['feasible_count'] += 1
                combination_stats[name]['instance_count'] += 1
                combination_stats[name]['all_costs'].extend(all_costs)
                combination_stats[name]['instance_results'].append(result)

                status = "✓"
                print(f"{status} Best: {best_cost_combo:.2f}, Avg: {avg_cost:.2f}, Time: {avg_time:.2f}s")

            else:
                result = {
                    "instance": instance["name"],
                    "instance_file": instance_file.name,
                    "method": name,
                    "best_cost": float('inf'),
                    "avg_cost": float('inf'),
                    "feasible": False
                }
                combination_stats[name]['instance_count'] += 1
                print(f"✗ All runs failed")

            all_results.append(result)
            instance_results.append(result)

        # Save instance-specific results
        instance_output_file = os.path.join(OUTPUT_DIR, f"{instance_file.stem}_results.json")
        with open(instance_output_file, "w") as f:
            json.dump(instance_results, f, indent=2)
        print(f"  ✅ Saved: {instance_output_file}")

    # ================================
    # Calculate Final Rankings
    # ================================
    print("\n" + "=" * 80)
    print("CALCULATING FINAL RANKINGS")
    print("=" * 80)

    rankings = []
    for name, stats in combination_stats.items():
        if stats['feasible_count'] > 0:
            avg_best_cost = stats['total_best_cost'] / stats['feasible_count']
            avg_avg_cost = stats['total_avg_cost'] / stats['feasible_count']
            avg_time = stats['total_time'] / stats['instance_count']
            feasibility_rate = stats['feasible_count'] / stats['instance_count']

            overall_std = np.std(stats['all_costs']) if stats['all_costs'] else 0

            rankings.append({
                'method': name,
                'avg_best_cost': round(avg_best_cost, 2),
                'avg_avg_cost': round(avg_avg_cost, 2),
                'overall_std': round(overall_std, 2),
                'avg_time': round(avg_time, 2),
                'feasible_count': stats['feasible_count'],
                'total_instances': stats['instance_count'],
                'feasibility_rate': round(feasibility_rate * 100, 2),
                'total_runs': len(stats['all_costs'])
            })

    # Sort by: feasibility rate (desc), then avg_best_cost (asc)
    rankings.sort(key=lambda x: (-x['feasibility_rate'], x['avg_best_cost']))

    # ================================
    # Save Results
    # ================================
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)

    with open(os.path.join(OUTPUT_DIR, "all_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"✅ Saved: {OUTPUT_DIR}/all_results.json ({len(all_results)} results)")

    with open(os.path.join(OUTPUT_DIR, "rankings.json"), "w") as f:
        json.dump(rankings, f, indent=2)
    print(f"✅ Saved: {OUTPUT_DIR}/rankings.json")

    if rankings:
        best = rankings[0]
        best_method = best['method']
        best_details = {
            'best_combination': best,
            'detailed_results': combination_stats[best_method]['instance_results'],
            'statistics': {
                'mean_cost': round(np.mean(combination_stats[best_method]['all_costs']), 2),
                'median_cost': round(np.median(combination_stats[best_method]['all_costs']), 2),
                'std_cost': round(np.std(combination_stats[best_method]['all_costs']), 2),
                'min_cost': round(min(combination_stats[best_method]['all_costs']), 2),
                'max_cost': round(max(combination_stats[best_method]['all_costs']), 2)
            }
        }

        with open(os.path.join(OUTPUT_DIR, "best_combination.json"), "w") as f:
            json.dump(best_details, f, indent=2)
        print(f"✅ Saved: {OUTPUT_DIR}/best_combination.json")

    # ================================
    # Print Summary
    # ================================
    print("\n" + "=" * 80)
    print("TOP 10 COMBINATIONS")
    print("=" * 80)
    print(f"{'Rank':<5} {'Method':<30} {'Avg Best':<12} {'Avg±Std':<15} {'Feasible':<12} {'Time':<10}")
    print("-" * 80)

    for i, rank in enumerate(rankings[:10], 1):
        feasible_str = f"{rank['feasible_count']}/{rank['total_instances']}"
        avg_std_str = f"{rank['avg_avg_cost']:.1f}±{rank['overall_std']:.1f}"
        print(f"{i:<5} {rank['method']:<30} {rank['avg_best_cost']:<12.2f} "
              f"{avg_std_str:<15} {feasible_str:<12} {rank['avg_time']:<10.2f}s")

    if rankings:
        print("\n" + "=" * 80)
        print("🏆 BEST COMBINATION")
        print("=" * 80)
        best = rankings[0]
        stats = best_details['statistics']
        print(f"Method: {best['method']}")
        print(f"Average Best Cost: {best['avg_best_cost']:.2f}")
        print(f"Average Cost (across all runs): {best['avg_avg_cost']:.2f}")
        print(f"Overall Std Dev: {best['overall_std']:.2f}")
        print(f"Feasibility Rate: {best['feasibility_rate']:.1f}%")
        print(f"Average Time: {best['avg_time']:.2f}s")
        print(f"Total Runs: {best['total_runs']}")
        print(f"\nDetailed Statistics:")
        print(f"  Mean: {stats['mean_cost']:.2f}")
        print(f"  Median: {stats['median_cost']:.2f}")
        print(f"  Min: {stats['min_cost']:.2f}")
        print(f"  Max: {stats['max_cost']:.2f}")
        print(f"  Std: {stats['std_cost']:.2f}")

    # ================================
    # Generate Visualizations
    # ================================
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)

    if rankings:
        fig, axes = plt.subplots(2, 2, figsize=(18, 12))

        # Plot 1: Average best cost comparison
        methods = [r['method'] for r in rankings[:10]]
        costs = [r['avg_best_cost'] for r in rankings[:10]]
        colors = ['green' if r['feasibility_rate'] == 100 else 'orange' for r in rankings[:10]]

        axes[0, 0].barh(methods, costs, color=colors)
        axes[0, 0].set_xlabel('Average Best Cost')
        axes[0, 0].set_title('Top 10: Average Best Cost')
        axes[0, 0].grid(axis='x', alpha=0.3)

        # Plot 2: Feasibility rate
        feasibility_rates = [r['feasibility_rate'] for r in rankings[:10]]
        axes[0, 1].barh(methods, feasibility_rates, color='steelblue')
        axes[0, 1].set_xlabel('Feasibility Rate (%)')
        axes[0, 1].set_title('Top 10: Feasibility Rate')
        axes[0, 1].set_xlim(0, 100)
        axes[0, 1].grid(axis='x', alpha=0.3)

        # Plot 3: Cost with error bars (avg ± std)
        avg_costs = [r['avg_avg_cost'] for r in rankings[:10]]
        stds = [r['overall_std'] for r in rankings[:10]]
        y_pos = np.arange(len(methods))
        axes[1, 0].barh(y_pos, avg_costs, xerr=stds, color='coral', alpha=0.7)
        axes[1, 0].set_yticks(y_pos)
        axes[1, 0].set_yticklabels(methods)
        axes[1, 0].set_xlabel('Average Cost ± Std Dev')
        axes[1, 0].set_title('Top 10: Robustness (lower std = more consistent)')
        axes[1, 0].grid(axis='x', alpha=0.3)

        # Plot 4: Execution time
        times = [r['avg_time'] for r in rankings[:10]]
        axes[1, 1].barh(methods, times, color='mediumpurple')
        axes[1, 1].set_xlabel('Average Time (seconds)')
        axes[1, 1].set_title('Top 10: Computational Efficiency')
        axes[1, 1].grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "comprehensive_comparison.png"),
                    dpi=150, bbox_inches='tight')
        print(f"✅ Saved: {OUTPUT_DIR}/comprehensive_comparison.png")

        plt.show()

    print("\n" + "=" * 80)
    print("✅ TESTING COMPLETE!")
    print(f"Results saved to: {OUTPUT_DIR}/")
    print("=" * 80)


# ================================
# Entry Point
# ================================
if __name__ == "__main__":
    import random

    run_multi_instance_test()