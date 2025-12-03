import os
import time
import csv
import matplotlib.pyplot as plt
from sudoku_board import SudokuBoard
from Backtrack_Solver import backtrack_solve
from CSP_solver import solve as csp_solve  

"""
Run all experiments across puzzle files and solver types
@param puzzle_files: list of puzzle file names
@param custom_flags: list of booleans, true if diagonal custom
@return: results as a list of dicts
"""
def run_experiment(puzzle_files, custom_flags):

    results = []

    for file_path, custom in zip(puzzle_files, custom_flags):
        board = SudokuBoard(file_path, custom=custom)

        # Plain backtracking 
        print(f"\nRunning Backtracking on {os.path.basename(file_path)} (custom={custom})")
        start = time.perf_counter()
        solved = backtrack_solve(board)
        end = time.perf_counter()
        results.append({
            "solver": "Backtracking",
            "file": os.path.basename(file_path),
            "custom": custom,
            "runtime": end - start,
            "nodes": board.backtrack_calls if hasattr(board, 'backtrack_calls') else "N/A",
            "constraint_checks": board.constraint_checks if hasattr(board, 'constraint_checks') else "N/A"
        })

        # Reset board for CSP
        board = SudokuBoard(file_path, custom=custom)

        print(f"\nRunning CSP on {os.path.basename(file_path)} (custom={custom})")
        start = time.perf_counter()
        csp_metrics = csp_solve(board)  # csp_solve should return a dict: runtime, configsProcessed, consistency, copying
        end = time.perf_counter()
        results.append({
            "solver": "CSP",
            "file": os.path.basename(file_path),
            "custom": custom,
            "runtime": end - start,
            "nodes": csp_metrics.get("configsProcessed", "N/A"),
            "constraint_checks": csp_metrics.get("constraint_checks", "N/A"),
            "consistency_time": csp_metrics.get("consistency", "N/A"),
            "copying_time": csp_metrics.get("copying", "N/A")
        })

    return results

def save_results_csv(results, filename="experiment_results.csv"):
    if not results:
        print("No results to save.")
        return

    # Get the union of all keys from all result dictionaries
    all_keys = set().union(*[r.keys() for r in results])

    # Makes sure every dictionary has all keys
    for r in results:
        for k in all_keys:
            if k not in r:
                r[k] = 0  # Fills missing metrics with 0

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(results)


def plot_results(results):
    # Separate solvers
    backtrack_runtimes = [r["runtime"] for r in results if r["solver"] == "Backtracking"]
    csp_runtimes = [r["runtime"] for r in results if r["solver"] == "CSP"]

    backtrack_nodes = [r["nodes"] for r in results if r["solver"] == "Backtracking"]
    csp_nodes = [r["nodes"] for r in results if r["solver"] == "CSP"]

    files = [r["file"] for r in results if r["solver"] == "Backtracking"]

    # Figure 1: Runtime Comparison
    plt.figure(figsize=(6, 4))
    plt.bar(["Backtracking", "CSP"], [sum(backtrack_runtimes)/len(backtrack_runtimes),
                                      sum(csp_runtimes)/len(csp_runtimes)], color=["orange", "green"])
    plt.ylabel("Average Runtime (s)")
    plt.title("Total Runtime Comparison")
    plt.savefig("figure_runtime.png")
    plt.show()

    #Figure 2: Search Effort
    plt.figure(figsize=(6, 4))
    plt.bar(["Backtracking", "CSP"], [sum(backtrack_nodes)/len(backtrack_nodes),
                                      sum(csp_nodes)/len(csp_nodes)], color=["orange", "green"])
    plt.yscale("log")
    plt.ylabel("Nodes Visited (log scale)")
    plt.title("Search Effort Reduction")
    plt.savefig("figure_nodes.png")
    plt.show()

"""
Currently just to test out Sudoku Board class. Might be used to run everything, and have the test functions in here
"""
def main():
    dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    puzzle_files = [
        os.path.join(dir, "data", "puzzle_standard_1.txt"),
        os.path.join(dir, "data", "puzzle_hard.txt"),
        os.path.join(dir, "data", "puzzle_custom_1.txt")
    ]
    custom_flags = [False, False, True]

    results = run_experiment(puzzle_files, custom_flags)
    save_results_csv(results)
    plot_results(results)
    
if __name__ == "__main__":
    main()