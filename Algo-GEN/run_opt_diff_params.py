import time
import matplotlib.pyplot as plt
import json
import sys
import os
from pathlib import Path
import numpy as np
from collections import defaultdict
import random

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
OUTPUT_DIR = "multi_instance_results_params"
RUNS_PER_COMBINATION = 5  # Reduced to save time with more parameter combos
SEED_START = 100

# Parameter grids to test
PARAMETER_CONFIGS = [
    # Balanced configurations
    {"pop_size": 100, "generations": 400, "px": 0.85, "pm": 0.2},
    {"pop_size": 120, "generations": 600, "px": 0.9, "pm": 0.25},  # Your current
    {"pop_size": 150, "generations": 800, "px": 0.9, "pm": 0.3},

    # High exploration
    {"pop_size": 80, "generations": 500, "px": 0.8, "pm": 0.35},

    # High exploitation
    {"pop_size": 200, "generations": 600, "px": 0.95, "pm": 0.15},
]


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


def get_operator_combinations():
    """Generate all operator combinations"""
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

    combinations = []
    for sel_name, sel_func in selection_methods:
        for cross_name, cross_func in crossover_methods:
            for mut_name, mut_func in mutation_methods:
                name = f"{sel_name}+{cross_name}+{mut_name}"
                combinations.append((name, sel_func, cross_func, mut_func))

    return combinations


def get_all_experiments():
    """Generate all experiments (operators + parameters)"""
    operator_combos = get_operator_combinations()
    experiments = []

    for op_name, sel, cross, mut in operator_combos:
        for idx, params in enumerate(PARAMETER_CONFIGS):
            exp_name = f"{op_name}|P{params['pop_size']}G{params['generations']}X{params['px']}M{params['pm']}"
            experiments.append({
                'name': exp_name,
                'operators': (op_name, sel, cross, mut),
                'params': params
            })

    return experiments


# ================================
# Main Testing Function
# ================================
def run_multi_instance_test():
    """Run comprehensive testing across all instances and combinations"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    experiments = get_all_experiments()
    instance_files = get_instance_files(INSTANCE_FOLDERS)

    if not instance_files:
        print("❌ No instance files found! Check your folder paths.")
        print(f"   Looking in: {INSTANCE_FOLDERS}")
        return

    print("=" * 80)
    print("COMPREHENSIVE GA TESTING - OPERATORS + PARAMETERS")
    print("=" * 80)
    print(f"Instances found: {len(instance_files)}")
    print(f"Operator combinations: {len(get_operator_combinations())}")
    print(f"Parameter configurations: {len(PARAMETER_CONFIGS)}")
    print(f"Total experiments: {len(experiments)}")
    print(f"Runs per experiment: {RUNS_PER_COMBINATION}")
    print(f"TOTAL RUNS: {len(instance_files) * len(experiments) * RUNS_PER_COMBINATION}")
    print("=" * 80)

    response = input("\n⚠️  This will take a LONG time. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return

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

    global_best = {
        'cost': float('inf'),
        'config': None,
        'instance': None,
        'solution': None
    }

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

        # Test each experiment
        for exp_idx, exp in enumerate(experiments, 1):
            name = exp['name']
            op_name, sel, cross, mut = exp['operators']
            params = exp['params']

            print(f"  [{exp_idx}/{len(experiments)}] {name[:60]}...", end=" ", flush=True)

            best_cost_combo = float("inf")
            best_solution_combo = None
            all_costs = []
            total_time = 0

            # Multiple runs for this experiment
            for run in range(RUNS_PER_COMBINATION):
                seed = SEED_START + run
                random.seed(seed)
                np.random.seed(seed)

                try:
                    best_chrom, best_cost, history, exec_time = genetic_algorithm(
                        instance,
                        dist,
                        selection=sel,
                        crossover=cross,
                        mutation=mut,
                        pop_size=params['pop_size'],
                        generations=params['generations'],
                        px=params['px'],
                        pm=params['pm']
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

                        # Update global best
                        if cost < global_best['cost']:
                            global_best['cost'] = cost
                            global_best['config'] = name
                            global_best['instance'] = instance["name"]
                            global_best['solution'] = sol
                            print(f"\n    🎯 NEW GLOBAL BEST: {cost:.2f} on {instance['name']}")

                    total_time += exec_time

                except Exception as e:
                    continue

            # Calculate statistics
            if all_costs:
                avg_cost = np.mean(all_costs)
                std_cost = np.std(all_costs)
                min_cost = min(all_costs)
                avg_time = total_time / RUNS_PER_COMBINATION

                gap = None
                if instance["optimal"] and instance["optimal"] > 0:
                    gap = ((best_cost_combo - instance["optimal"]) / instance["optimal"]) * 100

                result = {
                    "instance": instance["name"],
                    "instance_file": instance_file.name,
                    "config": name,
                    "operators": op_name,
                    "parameters": params,
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

                # Update stats
                combination_stats[name]['total_best_cost'] += best_cost_combo
                combination_stats[name]['total_avg_cost'] += avg_cost
                combination_stats[name]['total_time'] += avg_time
                combination_stats[name]['feasible_count'] += 1
                combination_stats[name]['instance_count'] += 1
                combination_stats[name]['all_costs'].extend(all_costs)
                combination_stats[name]['instance_results'].append(result)

                print(f"✓ Best: {best_cost_combo:.2f}, Avg: {avg_cost:.2f}")

            else:
                result = {
                    "instance": instance["name"],
                    "instance_file": instance_file.name,
                    "config": name,
                    "operators": op_name,
                    "parameters": params,
                    "best_cost": float('inf'),
                    "feasible": False
                }
                combination_stats[name]['instance_count'] += 1
                print(f"✗ Failed")

            all_results.append(result)
            instance_results.append(result)

        # Save instance-specific results
        instance_output_file = os.path.join(OUTPUT_DIR, f"{instance_file.stem}_results.json")
        with open(instance_output_file, "w") as f:
            json.dump(instance_results, f, indent=2)

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
                'config': name,
                'avg_best_cost': round(avg_best_cost, 2),
                'avg_avg_cost': round(avg_avg_cost, 2),
                'overall_std': round(overall_std, 2),
                'avg_time': round(avg_time, 2),
                'feasible_count': stats['feasible_count'],
                'total_instances': stats['instance_count'],
                'feasibility_rate': round(feasibility_rate * 100, 2),
                'total_runs': len(stats['all_costs'])
            })

    rankings.sort(key=lambda x: (-x['feasibility_rate'], x['avg_best_cost']))

    # ================================
    # Save Results
    # ================================
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)

    with open(os.path.join(OUTPUT_DIR, "all_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"✅ Saved: {OUTPUT_DIR}/all_results.json")

    with open(os.path.join(OUTPUT_DIR, "rankings.json"), "w") as f:
        json.dump(rankings, f, indent=2)
    print(f"✅ Saved: {OUTPUT_DIR}/rankings.json")

    with open(os.path.join(OUTPUT_DIR, "global_best.json"), "w") as f:
        json.dump({
            'best_cost': global_best['cost'],
            'best_config': global_best['config'],
            'best_instance': global_best['instance'],
            'solution': str(global_best['solution'])
        }, f, indent=2)
    print(f"✅ Saved: {OUTPUT_DIR}/global_best.json")

    if rankings:
        best = rankings[0]
        best_config = best['config']
        best_details = {
            'best_configuration': best,
            'detailed_results': combination_stats[best_config]['instance_results']
        }

        with open(os.path.join(OUTPUT_DIR, "best_configuration.json"), "w") as f:
            json.dump(best_details, f, indent=2)
        print(f"✅ Saved: {OUTPUT_DIR}/best_configuration.json")

    # ================================
    # Print Summary
    # ================================
    print("\n" + "=" * 80)
    print("🌟 GLOBAL BEST RESULT")
    print("=" * 80)
    print(f"Best Cost Ever: {global_best['cost']:.2f}")
    print(f"Configuration: {global_best['config']}")
    print(f"Instance: {global_best['instance']}")

    print("\n" + "=" * 80)
    print("TOP 15 CONFIGURATIONS (Averaged across all instances)")
    print("=" * 80)
    print(f"{'Rank':<5} {'Configuration':<80} {'Avg Best':<12} {'Feasible':<10}")
    print("-" * 120)

    for i, rank in enumerate(rankings[:15], 1):
        feasible_str = f"{rank['feasible_count']}/{rank['total_instances']}"
        config_short = rank['config'][:78]
        print(f"{i:<5} {config_short:<80} {rank['avg_best_cost']:<12.2f} {feasible_str:<10}")

    if rankings:
        print("\n" + "=" * 80)
        print("🏆 BEST OVERALL CONFIGURATION")
        print("=" * 80)
        best = rankings[0]
        print(f"Configuration: {best['config']}")
        print(f"Average Best Cost: {best['avg_best_cost']:.2f}")
        print(f"Average Cost: {best['avg_avg_cost']:.2f} ± {best['overall_std']:.2f}")
        print(f"Feasibility Rate: {best['feasibility_rate']:.1f}%")
        print(f"Average Time: {best['avg_time']:.2f}s")

    print("\n" + "=" * 80)
    print("✅ TESTING COMPLETE!")
    print(f"Results saved to: {OUTPUT_DIR}/")
    print("=" * 80)


if __name__ == "__main__":
    run_multi_instance_test()