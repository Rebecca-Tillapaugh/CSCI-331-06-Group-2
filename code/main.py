import os
import time
import csv
import statistics
import matplotlib.pyplot as plt
from sudoku_board import SudokuBoard
from Backtrack_Solver import backtrack_solve
from CSP_solver import solve as csp_solve


puzzle_files_info = [
    # (file_path, custom_flag, difficulty_label)
    
    # Easy (5 Puzzles)
    ("puzzle_easy_1.txt", False, "Easy"),
    ("puzzle_easy_2.txt", False, "Easy"),
    ("puzzle_easy_3.txt", False, "Easy"),
    ("puzzle_easy_4.txt", False, "Easy"),
    ("puzzle_easy_5.txt", False, "Easy"),

    # Standard Medium (5 Puzzles)
    ("puzzle_std_med_1.txt", False, "Medium"),
    ("puzzle_std_med_2.txt", False, "Medium"),
    ("puzzle_std_med_3.txt", False, "Medium"),
    ("puzzle_std_med_4.txt", False, "Medium"),
    ("puzzle_std_med_5.txt", False, "Medium"),

    # Standard Hard (10 Puzzles) 
    ("puzzle_std_hard_1.txt", False, "Hard"),
    ("puzzle_std_hard_2.txt", False, "Hard"),
    ("puzzle_std_hard_3.txt", False, "Hard"),
    ("puzzle_std_hard_4.txt", False, "Hard"),
    ("puzzle_std_hard_5.txt", False, "Hard"),
    ("puzzle_std_hard_6.txt", False, "Hard"),
    ("puzzle_std_hard_7.txt", False, "Hard"),
    ("puzzle_std_hard_8.txt", False, "Hard"),
    ("puzzle_std_hard_9.txt", False, "Hard"),
    ("puzzle_std_hard_10.txt", False, "Hard"),

    # Custom Diagonal Medium (5 Puzzles)
    ("puzzle_custom_med_1.txt", True, "Custom Medium"),
    ("puzzle_custom_med_2.txt", True, "Custom Medium"),
    ("puzzle_custom_med_3.txt", True, "Custom Medium"),
    ("puzzle_custom_med_4.txt", True, "Custom Medium"),
    ("puzzle_custom_med_5.txt", True, "Custom Medium"),

    # Custom Diagonal Hard (10 Puzzles)
    ("puzzle_custom_hard_1.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_2.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_3.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_4.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_5.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_6.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_7.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_8.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_9.txt", True, "Custom Hard"),
    ("puzzle_custom_hard_10.txt", True, "Custom Hard"),
]

# Runs the experiment
def run_experiment(puzzle_files_info):
    results = []

    for file_path, custom, difficulty in puzzle_files_info:
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(dir_path, "data", file_path)
        board = SudokuBoard(full_path, custom=custom)

        # Plain Backtracking
        print(f"\nRunning Backtracking on {file_path} (custom={custom})")
        bt_metrics = backtrack_solve(board)

        results.append({
            "solver": "Backtracking",
            "file": file_path,
            "custom": custom,
            "difficulty": difficulty,
            "runtime": bt_metrics["runtime"],
            "assignments": bt_metrics.get("assignments", 0),
            "backtracks": bt_metrics.get("backtracks", 0),
            "constraint_checks": bt_metrics.get("constraint_checks", 0),
            "consistency_time": bt_metrics.get("consistency_time", 0),
            "copying_time": bt_metrics.get("copying_time", 0)
        })

        # Reset board for CSP
        board = SudokuBoard(full_path, custom=custom)

        # CSP
        print(f"\nRunning CSP on {file_path} (custom={custom})")
        csp_metrics = csp_solve(board)

        configs_processed = csp_metrics.get("configsProcessed", 0)
        configs_generated = csp_metrics.get("configsGenerated", 0)
        csp_backtracks = configs_generated - configs_processed

        results.append({
            "solver": "CSP",
            "file": file_path,
            "custom": custom,
            "difficulty": difficulty,
            "runtime": csp_metrics["runtime"],
            "assignments": configs_processed,
            "backtracks": csp_backtracks,
            "constraint_checks": csp_metrics.get("constraint_checks", 0),
            "consistency_time": csp_metrics.get("consistency_time", 0),
            "copying_time": csp_metrics.get("copying_time", 0)
        })

    return results

def save_results_csv(results, filename="experiment_results.csv"):
    if not results:
        print("No results to save.")
        return

    all_keys = set().union(*[r.keys() for r in results])
    for r in results:
        for k in all_keys:
            if k not in r:
                r[k] = 0

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"Results saved to {filename}")

def aggregate_results_by_difficulty(results):
    grouped_data = {}
    for r in results:
        key = (r['difficulty'], r['solver'])
        if key not in grouped_data:
            grouped_data[key] = {'runtime': [], 'assignments': [], 'backtracks': []}
        grouped_data[key]['runtime'].append(r['runtime'])
        grouped_data[key]['assignments'].append(r['assignments'])
        grouped_data[key]['backtracks'].append(r['backtracks'])

    aggregated = []
    difficulty_order = ["Easy", "Medium", "Hard", "Evil"]
    for difficulty in difficulty_order:
        for solver in ["Backtracking", "CSP"]:
            key = (difficulty, solver)
            if key in grouped_data:
                data = grouped_data[key]
                if not data['runtime']:
                    continue
                aggregated.append({
                    "difficulty": difficulty,
                    "solver": solver,
                    "avg_runtime": statistics.mean(data['runtime']),
                    "avg_assignments": statistics.mean(data['assignments']),
                    "avg_backtracks": statistics.mean(data['backtracks']),
                })
    return aggregated

def plot_aggregate_results(aggregated_results, metric_key, title, ylabel, filename):
    difficulty_order = ["Easy", "Medium", "Hard", "Evil"]
    difficulties = [d for d in difficulty_order if d in [r['difficulty'] for r in aggregated_results]]

    bt_data = [r[metric_key] for d in difficulties for r in aggregated_results if r['difficulty'] == d and r['solver'] == 'Backtracking']
    csp_data = [r[metric_key] for d in difficulties for r in aggregated_results if r['difficulty'] == d and r['solver'] == 'CSP']

    x = range(len(difficulties))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width/2 for i in x], bt_data, width, label='Backtracking', color='#1f77b4')
    ax.bar([i + width/2 for i in x], csp_data, width, label='CSP (FC+MRV+LCV)', color='#ff7f0e')

    ax.set_ylabel(ylabel)
    ax.set_xlabel("Puzzle Difficulty")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(difficulties)

    if 'backtracks' in metric_key or 'assignments' in metric_key:
        ax.set_yscale('log')

    ax.legend()
    fig.tight_layout()
    plt.savefig(filename)
    plt.show()

def plot_aggregate_runtime(aggregated_results):
    plot_aggregate_results(aggregated_results, 'avg_runtime',
                           "Average Runtime by Difficulty", "Runtime (s)",
                           "figure_aggregate_runtime.png")

def plot_aggregate_assignments(aggregated_results):
    plot_aggregate_results(aggregated_results, 'avg_assignments',
                           "Average Assignments (Search Space Size)", "Assignments (Log Scale)",
                           "figure_aggregate_assignments.png")

def plot_aggregate_backtracks(aggregated_results):
    plot_aggregate_results(aggregated_results, 'avg_backtracks',
                           "Average Backtracks (Pruning Success)", "Backtracks (Log Scale)",
                           "figure_aggregate_backtracks.png")

# Summary of stats
def summary_statistics(results):
    for solver in ["Backtracking", "CSP"]:
        solver_results = [r for r in results if r["solver"] == solver]
        runtimes = [r["runtime"] for r in solver_results]
        assignments = [r["assignments"] for r in solver_results]
        backtracks = [r["backtracks"] for r in solver_results]
        print(f"\n{solver} Summary (Raw Data):")
        print(f"Average runtime: {statistics.mean(runtimes):.4f}s, stdev: {statistics.stdev(runtimes) if len(runtimes) > 1 else 0:.4f}")
        print(f"Average assignments: {statistics.mean(assignments):.2f}")
        print(f"Average backtracks: {statistics.mean(backtracks):.2f}")


def main():
    results = run_experiment(puzzle_files_info)
    save_results_csv(results)

    aggregated_data = aggregate_results_by_difficulty(results)
    plot_aggregate_runtime(aggregated_data)
    plot_aggregate_assignments(aggregated_data)
    plot_aggregate_backtracks(aggregated_data)

    summary_statistics(results)

if __name__ == "__main__":
    main()