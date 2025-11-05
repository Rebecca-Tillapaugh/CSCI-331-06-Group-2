import os
from sudoku_board import SudokuBoard
from Backtrack_Solver import backtrack_solve


"""
Currently just to test out Sudoku Board class. Might be used to run everything, and have the test functions in here
"""
def main():
    dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(dir, "data", "puzzle_standard_1.txt")

    # Initialize and test board
    board = SudokuBoard(file_path, custom=False)

    print("Initial Sudoku Board:\n")
    board.print_board()

    empty = board.find_empty()
    if empty is not None:
        print("First empty cell found at:", empty)
    else:
        print("Board is full!")

    print("Solving board with backtracking...")
    backtrack_solve(board)
    
    
if __name__ == "__main__":
    main()