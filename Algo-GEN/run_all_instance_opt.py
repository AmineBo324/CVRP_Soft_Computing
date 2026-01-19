import time
import matplotlib.pyplot as plt
import json
import sys
import os
from pathlib import Path
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

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
# CONFIGURATION - OPTIMIZED FOR SPEED
# ================================
INSTANCE_FOLDERS = ["../instances/A", "../instances/B"]
OUTPUT_DIR = "multi_instance_results_optimized"
RUNS_PER_COMBINATION = 3  # Reduced from 10 to 3
SEED_START = 100

# Reduced GA parameters for speed
FAST_PARAMS = {
    'pop_size': 60,  # Reduced from 120
    'generations': 200,  # Reduced from 600
    'px': 0.9,
    'pm': 0.25
}

# Enable parallel processing
USE_PARALLEL = True
NUM_WORKERS = max(1, mp.cpu_count() - 1)  # Leave 1 core free


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
    return files


def get_experiments():
    """Generate all experiment combinations"""
    selection_methods = [
        ("Tournament", tournament_selection),
        ("Rank", rank_selection),
        ("Roulette", roulette_wheel_selection),
        # Removed slower methods for speed
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
# Parallel Worker Function
# ================================
def run_single_experiment(args):
    """Worker function for parallel execution"""
    instance_file, exp_tuple, run_idx = args
    name, sel, cross, mut = exp_tuple

    import random

    try:
        instance = read_cvrp_instance(str(instance_file))
        dist = build_distance_matrix(instance["coords"])

        seed = SEED_START + run_idx
        random.seed(seed)
        np.random.seed(seed)

        best_chrom, best_cost, history, exec_time = genetic_algorithm(
            instance,
            dist,
            selection=sel,
            crossover=cross,
            mutation=mut,
            pop_size=FAST_PARAMS['pop_size'],
            generations=FAST_PARAMS['generations'],
            px=FAST_PARAMS['px'],
            pm=FAST_PARAMS['pm']
        )

        sol = decode(best_chrom, instance)
        sol = local_search_solution(sol, dist)
        cost = solution_cost(sol, dist)

        feasible = is_solution_feasible(
            sol,
            demands=instance["demands"],
            capacity=instance["capacity"],
            depot=instance["depot"]
        )

        return {
            'instance_name': instance["name"],
            'method': name,
            'cost': cost if feasible else float('inf'),
            'time': exec_time,
            'feasible': feasible,
            'optimal': instance.get("optimal")
        }
    except Exception as e:
        return {
            'instance_name': instance_file.name,
            'method': name,
            'cost': float('inf'),
            'time': 0,
            'feasible': False,
            'error': str(e)
        }


# ================================
# Main Testing Function
# ================================
def run_multi_instance_test():
    """Run comprehensive testing across all instances and combinations"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    experiments = get_experiments()
    instance_files = get_instance_files(INSTANCE_FOLDERS)

    if not instance_files:
        print("❌ No instance files found!")
        return

    print("=" * 80)
    print("FAST MULTI-INSTANCE GA TESTING")
    print("=" * 80)
    print(f"Instances: {len(instance_files)}")
    print(f"Combinations: {len(experiments)}")
    print(f"Runs per combination: {RUNS_PER_COMBINATION}")
    print(f"GA Parameters: pop={FAST_PARAMS['pop_size']}, gen={FAST_PARAMS['generations']}")
    print(f"Parallel workers: {NUM_WORKERS if USE_PARALLEL else 'Disabled'}")
    print(f"Total runs: {len(instance_files) * len(experiments) * RUNS_PER_COMBINATION}")
    print("=" * 80)

    combination_stats = defaultdict(lambda: {
        'total_best_cost': 0,
        'total_avg_cost': 0,
        'total_time': 0,
        'feasible_count': 0,
        'instance_count': 0,
        'all_costs': [],
        'instance_results': []
    })

    all_results = []
    start_time = time.time()

    # ================================
    # Parallel Processing
    # ================================
    if USE_PARALLEL:
        print("\n🚀 Running in parallel mode...")

        # Prepare all jobs
        jobs = []
        for instance_file in instance_files:
            for exp_tuple in experiments:
                for run_idx in range(RUNS_PER_COMBINATION):
                    jobs.append((instance_file, exp_tuple, run_idx))

        total_jobs = len(jobs)
        completed = 0

        # Execute in parallel
        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(run_single_experiment, job): job for job in jobs}

            for future in as_completed(futures):
                result = future.result()
                completed += 1

                if completed % 10 == 0 or completed == total_jobs:
                    elapsed = time.time() - start_time
                    eta = (elapsed / completed) * (total_jobs - completed)
                    print(f"Progress: {completed}/{total_jobs} ({100 * completed / total_jobs:.1f}%) "
                          f"| Elapsed: {elapsed / 60:.1f}min | ETA: {eta / 60:.1f}min")

                all_results.append(result)

    # ================================
    # Sequential Processing (fallback)
    # ================================
    else:
        print("\n⚙️  Running in sequential mode...")
        total_jobs = len(instance_files) * len(experiments) * RUNS_PER_COMBINATION
        completed = 0

        for instance_file in instance_files:
            for exp_tuple in experiments:
                for run_idx in range(RUNS_PER_COMBINATION):
                    result = run_single_experiment((instance_file, exp_tuple, run_idx))
                    all_results.append(result)
                    completed += 1

                    if completed % 10 == 0:
                        elapsed = time.time() - start_time
                        eta = (elapsed / completed) * (total_jobs - completed)
                        print(f"Progress: {completed}/{total_jobs} | ETA: {eta / 60:.1f}min")

    # ================================
    # Process Results
    # ================================
    print("\n" + "=" * 80)
    print("PROCESSING RESULTS")
    print("=" * 80)

    # Group results by instance and method
    instance_method_results = defaultdict(lambda: defaultdict(list))

    for result in all_results:
        if result['feasible']:
            instance_name = result['instance_name']
            method = result['method']
            instance_method_results[instance_name][method].append(result['cost'])

    # Calculate statistics
    for instance_name, methods in instance_method_results.items():
        for method, costs in methods.items():
            if costs:
                best_cost = min(costs)
                avg_cost = np.mean(costs)
                std_cost = np.std(costs)

                # Find optimal for gap calculation
                optimal = None
                for r in all_results:
                    if r['instance_name'] == instance_name and r.get('optimal'):
                        optimal = r['optimal']
                        break

                gap = None
                if optimal and optimal > 0:
                    gap = ((best_cost - optimal) / optimal) * 100

                result_entry = {
                    "instance": instance_name,
                    "method": method,
                    "best_cost": round(best_cost, 2),
                    "avg_cost": round(avg_cost, 2),
                    "std_cost": round(std_cost, 2),
                    "gap_from_optimal": round(gap, 2) if gap else None,
                    "optimal": optimal
                }

                combination_stats[method]['total_best_cost'] += best_cost
                combination_stats[method]['total_avg_cost'] += avg_cost
                combination_stats[method]['feasible_count'] += 1
                combination_stats[method]['instance_count'] += 1
                combination_stats[method]['all_costs'].extend(costs)
                combination_stats[method]['instance_results'].append(result_entry)

    # ================================
    # Calculate Rankings
    # ================================
    rankings = []
    for name, stats in combination_stats.items():
        if stats['feasible_count'] > 0:
            avg_best_cost = stats['total_best_cost'] / stats['feasible_count']
            avg_avg_cost = stats['total_avg_cost'] / stats['feasible_count']
            feasibility_rate = stats['feasible_count'] / len(instance_files)
            overall_std = np.std(stats['all_costs']) if stats['all_costs'] else 0

            rankings.append({
                'method': name,
                'avg_best_cost': round(avg_best_cost, 2),
                'avg_avg_cost': round(avg_avg_cost, 2),
                'overall_std': round(overall_std, 2),
                'feasible_count': stats['feasible_count'],
                'total_instances': len(instance_files),
                'feasibility_rate': round(feasibility_rate * 100, 2),
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
    print(f"✅ Saved: all_results.json")

    with open(os.path.join(OUTPUT_DIR, "rankings.json"), "w") as f:
        json.dump(rankings, f, indent=2)
    print(f"✅ Saved: rankings.json")

    if rankings:
        best_method = rankings[0]['method']
        best_details = {
            'best_combination': rankings[0],
            'detailed_results': combination_stats[best_method]['instance_results']
        }

        with open(os.path.join(OUTPUT_DIR, "best_combination.json"), "w") as f:
            json.dump(best_details, f, indent=2)
        print(f"✅ Saved: best_combination.json")

    # ================================
    # Print Summary
    # ================================
    total_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total execution time: {total_time / 60:.1f} minutes")
    print(f"Average time per instance: {total_time / len(instance_files):.1f} seconds")

    print("\n" + "=" * 80)
    print("TOP 10 COMBINATIONS")
    print("=" * 80)
    print(f"{'Rank':<5} {'Method':<30} {'Avg Best':<12} {'Feasible':<12} {'Gap':<10}")
    print("-" * 80)

    for i, rank in enumerate(rankings[:10], 1):
        feasible_str = f"{rank['feasible_count']}/{rank['total_instances']}"
        print(f"{i:<5} {rank['method']:<30} {rank['avg_best_cost']:<12.2f} {feasible_str:<12} "
              f"{rank['overall_std']:<10.2f}")

    if rankings:
        print("\n" + "=" * 80)
        print("🏆 BEST COMBINATION")
        print("=" * 80)
        best = rankings[0]
        print(f"Method: {best['method']}")
        print(f"Average Best Cost: {best['avg_best_cost']:.2f}")
        print(f"Feasibility Rate: {best['feasibility_rate']:.1f}%")
        print(f"Standard Deviation: {best['overall_std']:.2f}")

    print("\n" + "=" * 80)
    print("✅ TESTING COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    import random

    run_multi_instance_test()