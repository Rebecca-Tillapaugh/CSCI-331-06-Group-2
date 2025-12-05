from sudoku_board import SudokuBoard
import time
import os

# Performance counters for plain backtracking
backtrack_calls = 0
backtrack_count = 0

# Additional metrics (to match CSP)
assignment_count = 0
constraint_checks = 0


# Performs backtracking to solve Sudoku Board
def backtrack(board: SudokuBoard) -> bool:
    global backtrack_calls, backtrack_count, assignment_count, constraint_checks
    backtrack_calls += 1

    # Find next empty cell
    empty = board.find_empty()    
    if not empty:
        return True
    
    row, col = empty
    for num in range(1, 10):

        # Track constraint checks (closest equivalent to CSP's consistency work)
        constraint_checks += 1

        if board.is_valid_move(row, col, num):

            # Count assignments (first time placing the value)
            assignment_count += 1

            board.grid[row][col] = num
            if backtrack(board):
                return True

            backtrack_count += 1
            board.grid[row][col] = 0

    return False


def backtrack_solve(board: SudokuBoard):
    global backtrack_calls, backtrack_count, assignment_count, constraint_checks
    backtrack_calls = 0
    backtrack_count = 0
    assignment_count = 0
    constraint_checks = 0

    start_time = time.time()

    solved = backtrack(board)

    end_time = time.time()
    total_time = end_time - start_time

    print("\n--- Backtracking Performance ---")
    print(f"Runtime: {total_time:.4f} seconds")
    print(f"Backtrack calls: {backtrack_calls}")
    print(f"Backtracks made: {backtrack_count}")
    print(f"Assignments: {assignment_count}")
    print(f"Constraint checks: {constraint_checks}")

    if solved:
        print("\nSudoku solved using Backtracking.")
        board.print_board()
    else:
        print("\nNo solution found using Backtracking.")

    # Return metrics dictionary with same keys as CSP
    return {
        "solved": solved,
        "runtime": total_time,
        "backtrack_calls": backtrack_calls,
        "backtracks": backtrack_count,
        "assignments": assignment_count,      # NEW
        "constraint_checks": constraint_checks,  # NEW
        "consistency_time": 0,   # dummy since backtracking has no forward checking
        "copying_time": 0,       # dummy since backtracking has no state copying
        "finalBoard": board
    }

if __name__ == "__main__":
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(directory, "data", "puzzle_hard.txt")

    board = SudokuBoard(file_path)

    print("Initial Sudoku Board:")
    board.print_board()

    backtrack_solve(board)