class SudokuBoard:
    def __init__(self, board_file, custom=False):
        """
        Initializes the Sudoku board from a text file.
        @param board file: Path to the puzzle text file
        @param custom: Boolean flag indicating if this is a customized Sudoku (haven't implemented it yet)
        """
        self.grid = self.load_board(board_file)
        self.custom = custom
        self.size = 9  # Standard Sudoku board size (9x9)
        self.box_size = 3  # Size of the sub boxes (3x3)

    def load_board(self, filename):
        """
        Loads a Sudoku puzzle from a .txt file.
        Each line should have 9 digits (Domain: 0-9, 0 represents empty cell)
        """
        board = []
        with open(filename, 'r') as f:
            for line in f:
                row = []
                for ch in line.strip():
                    if ch.isdigit():
                        row.append(int(ch))
                    else:
                        row.append(0)
                board.append(row)
        return board

    def print_board(self):
        """
        Prints the Sudoku board
        """
        for i in range(self.size):
            if i % 3 == 0 and i != 0:
                print("-" * 21)
            for j in range(self.size):
                if j % 3 == 0 and j != 0:
                    print("|", end=" ")
                value = self.grid[i][j]
                if value != 0:
                    print(value, end=" ")
                else:
                    print(".", end=" ")
            print()
        print()

    def find_empty(self):
        """
        Finds the next empty cell on the board.
        Returns a tuple (row, col) or None if board is full.
        """
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 0:
                    return (i, j)
        return None

    def is_valid_move(self, row, col, num):
        """
        Checks whether placing a 'num' at (row, col) is a valid move.
        Additonal validity checks if it's flagged as a 'customized' board (Place holder for now)
        """

        # Row check
        for j in range(self.size):
            if self.grid[row][j] == num:
                return False

        # Column check
        for i in range(self.size):
            if self.grid[i][col] == num:
                return False

        # Box check
        start_row = (row // self.box_size) * self.box_size
        start_col = (col // self.box_size) * self.box_size
        for i in range(start_row, start_row + self.box_size):
            for j in range(start_col, start_col + self.box_size):
                if self.grid[i][j] == num:
                    return False

        # Placeholder for custom rule
        if self.custom:
            # Implement additional validation logic here
            pass

        return True

    def is_solved(self):
        """
        Checks if the board is completely filled and valid.
        """
        for row in range(self.size):
            for col in range(self.size):
                num = self.grid[row][col]
                if num == 0 or not self.is_valid_move(row, col, num):
                    return False
        return True