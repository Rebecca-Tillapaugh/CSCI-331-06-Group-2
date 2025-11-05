from sudoku_board import SudokuBoard
from CSP_solver import convert, CSPNode, enforceConsistency
import time
import os

# Performance counters for plain backtracking
backtrack_calls = 0
backtrack_count = 0

# Performs backtracking to solve Soduku Board
def backtrack(board: SudokuBoard, CSPDict: dict[tuple[int, int], 'CSPNode']) -> bool:

    global backtrack_calls, backtrack_count
    backtrack_calls += 1

    # Find next empty cell
    empty = []
    for pos, node in CSPDict.items():
        if node.assignedValue is None:
            empty.append((pos, node))
    
    # Check if puzzle has been solved
    if not empty:
        return True
    
    # Pick variable with smallest domain
    pos, node = min(empty, key=lambda item: len(item[1].possibleValues))
    row, col = pos

    for value in sorted(node.possibleValues):
        # Check if assignment is valid
        if all(neighbor.assignedValue != value for neighbor in node.neighbors):
            
            node.assignValue(value)
            board.grid[row][col] = value

            # Store original domains for backtracking
            old_domains = {}
            for n in node.neighbors:
                old_domains[n] = n.possibleValues.copy()
            
            # Delete value from neighbor domains
            for neighbor in node.neighbors:
                neighbor.restrict(value)

            if backtrack(board, CSPDict):
                return True

            # Backtrack - undo domain changes
            backtrack_count += 1
            node.assignedValue = None
            board.grid[row][col] = 0
            for neighbor, old_domain in old_domains.items():
                neighbor.possibleValues = old_domain.copy()

    # Invalid solution
    return False


def backtrack_solve(board: SudokuBoard):
    
    global backtrack_calls, backtrack_count
    backtrack_calls = 0
    backtrack_count = 0
    start_time = time.time()

    # Convert to CSP and keep consistent
    CSPDict = convert(board)
    enforceConsistency(CSPDict)
    solved = backtrack(board, CSPDict)

    end_time = time.time()
    total_time = end_time - start_time

    print("\n--- Backtracking Performance ---")
    print(f"Runtime: {total_time:.4f} seconds")
    print(f"Backtrack calls: {backtrack_calls}")
    print(f"Backtracks made: {backtrack_count}")

    if solved:
        print("\nSudoku solved using Backtracking.")
        board.print_board()
    else:
        print("\nNo solution found using Backtracking.")
    
    return solved

if __name__ == "__main__":
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(directory, "data", "puzzle_standard_1.txt")

    board = SudokuBoard(file_path)

    backtrack_solve(board)