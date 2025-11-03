import os
from collections import deque

from sudoku_board import SudokuBoard

ONE_TO_NINE = {1, 2, 3, 4, 5, 6, 7, 8 ,9}

class CSPNode:
    id : int
    assignedValue : int | None
    domain : set[int]
    possibleValues : set[int]
    neighbors : set

    def __init__(self, id : int, domain : set[int], assignedValue : int =None):
        self.id = id
        self.assignedValue = assignedValue
        self.domain = domain
        self.possibleValues = domain
        self.neighbors = set()

    def hasFinalValue(self):
        return len(self.possibleValues) == 1

    def isDeadEnd(self):
        return len(self.possibleValues) == 0

    def addNeighbors(self, *neighborsToAdd):
        self.neighbors.update(neighborsToAdd)

    def assignValue(self, value : int):
        if value in self.possibleValues:
            self.assignedValue = value
        else:
            print(f"CSP: Tried to assign invalid value ({value}) to node with available domain {self.possibleValues}")

    def restrict(self, *restrictions) -> bool:
        prevLen = len(self.possibleValues)
        self.possibleValues.difference_update(restrictions)
        restrictionMade = len(self.possibleValues) < prevLen

        return restrictionMade

    def __repr__(self):
        return str(self.possibleValues)

    def __hash__(self):
        return self.id

# Type alias for the standard data format for CSP Nodes representing a SudokuBoard
# Dict where the key is a (row, col) tuple of the cell and the value is the CSP Node of the cell
CSPBoard = dict[tuple[int, int], CSPNode]

def convert(board : SudokuBoard) -> CSPBoard:
    CSPDict = {}
    nodeId = 0
    for i, row in enumerate(board.grid):
        for j, value in enumerate(row):
            if value != 0:
                node = CSPNode(nodeId,{value}, assignedValue=value)
            else:
                node = CSPNode(nodeId, ONE_TO_NINE.copy())
            CSPDict[i, j] = node
            nodeId += 1

    for (thisRow, thisCol), node in CSPDict.items():
        node.addNeighbors(*[CSPDict[thisRow, col] for col in set(range(board.size)).difference({thisCol})])
        node.addNeighbors(*[CSPDict[row, thisCol] for row in set(range(board.size)).difference({thisRow})])

        start_row = (thisRow // board.box_size) * board.box_size
        start_col = (thisCol // board.box_size) * board.box_size
        for i in range(start_row, start_row + board.box_size):
            for j in range(start_col, start_col + board.box_size):
                if (i, j) != (thisRow, thisCol):
                    node.addNeighbors(CSPDict[i, j])

    return CSPDict

def enforceConsistency(board : CSPBoard) -> bool:
    stillToCheck = deque(board.values())
    inQueue = set(board.values())
    while len(stillToCheck) > 0:
        current = stillToCheck.popleft()
        inQueue.remove(current)

        revised = False
        for neighbor in current.neighbors:
            # Add bad vals to this set for removal later so the set doesn't change while under iteration
            invalidVals = set()
            for value in current.possibleValues:
                if value in neighbor.possibleValues and neighbor.hasFinalValue():
                    # Assigning value to current would leave neighbor with no possible values
                    invalidVals.add(value)
                    revised = True
            current.restrict(*invalidVals)

        if revised:
            if current.isDeadEnd():
                return False
            # Re-check all neighbors not already in the queue against this revised domain
            stillToCheck.extend([n for n in current.neighbors if n not in inQueue])
            inQueue.update(current.neighbors)
    return True


def solve(board : SudokuBoard):
    CSPDict = convert(board)
    consistent = enforceConsistency(CSPDict)
    if consistent:
        for (row, col), node in CSPDict.items():
            if node.hasFinalValue():
                board.grid[row][col] = [*node.possibleValues][0]
        board.print_board()


# Performs backtracking to solve Soduku Board
def backtrack(board: SudokuBoard, CSPDict: dict[tuple[int, int], 'CSPNode']) -> bool:

    # board is our soduko board we are trying to solve from the soduko_board file

    # CSPDict is a dictionary with key being the location of the cell and the value being the
    # CSPNode corresponding to the cell (with id, value, etc.)

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
        if all(value not in neighbor.possibleValues or neighbor.assignedValue is None for neighbor in node.neighbors):
            
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
            node.assignedValue = None
            board.grid[row][col] = 0
            for neighbor, old_domain in old_domains.items():
                neighbor.possibleValues = old_domain.copy()

    # Invalid solution
    return False


def backtrack_solve(board: SudokuBoard):

    # Convert to CSP and keep consistent
    CSPDict = convert(board)
    enforceConsistency(CSPDict)
    solved = backtrack(board, CSPDict)

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

    solve(board)