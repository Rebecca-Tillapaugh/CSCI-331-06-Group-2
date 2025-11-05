import os
import time

from collections import deque
from heapq import heapify, heappop
from math import sqrt

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
        self.possibleValues = domain.copy()
        self.neighbors = set()

    def hasFinalValue(self):
        return len(self.possibleValues) == 1

    def isDeadEnd(self):
        return len(self.possibleValues) == 0

    def addNeighbors(self, *neighborsToAdd):
        self.neighbors.update(neighborsToAdd)
        self.neighbors.difference_update([self])

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

    def copy(self):
        return CSPNode(self.id, self.domain, self.assignedValue)

    def __repr__(self):
        return str(self.possibleValues)

    def __hash__(self):
        return self.id

    def __lt__(self, other):
        return len(self.possibleValues) - len(other.possibleValues)

class CSPBoard:
    grid : list[list[CSPNode|None]]
    size : int
    boxSize : int

    def __init__(self, size:int, boxSize:int):
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self.size = size
        self.boxSize = boxSize

    def getAllNodes(self):
        allNodes = []
        for row in self.grid:
            allNodes.extend(row)
        return allNodes

    def assignNeighbors(self):
        for rowI, row in enumerate(self.grid):
            for colI, node in enumerate(row):
                # Same row
                node.addNeighbors(*row)
                # Same col
                node.addNeighbors(*[self.grid[row][colI] for row in range(len(self.grid))])

                # Same box
                start_row = (rowI // self.boxSize) * self.boxSize
                start_col = (colI // self.boxSize) * self.boxSize
                for i in range(start_row, start_row + self.boxSize):
                    for j in range(start_col, start_col + self.boxSize):
                        node.addNeighbors(self.grid[i][j])

    def copy(self):
        copy = CSPBoard(self.size, self.boxSize)
        for i, row in enumerate(self.grid):
            for j, node in enumerate(row):
                copy.grid[i][j] = node.copy()
        return copy

    def makeMove(self, cellToChange : CSPNode, val : int):
        copyBoard = self.copy()

        for node in copyBoard.getAllNodes():
            if node.id == cellToChange.id:
                node.assignValue(val)

        return copyBoard

    def enforceConsistency(self) -> bool:
        stillToCheck = deque()

        for row in self.grid:
            for node in row:
                stillToCheck.append(node)

        inQueue = set(stillToCheck)

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


def convert(baseBoard : SudokuBoard) -> CSPBoard:
    board = CSPBoard(baseBoard.size, baseBoard.box_size)
    nodeId = 0
    for i, row in enumerate(baseBoard.grid):
        for j, value in enumerate(row):
            if value != 0:
                node = CSPNode(nodeId,{value}, assignedValue=value)
            else:
                node = CSPNode(nodeId, ONE_TO_NINE.copy())
            board.grid[i][j] = node
            nodeId += 1

    board.assignNeighbors()

    return board

def solve(baseBoard : SudokuBoard):
    board = convert(baseBoard)

    # Basic approach which only does forward checking on initial state. Solves iff every resulting node has only one
    # possibility afterward (currently working. Solves puzzle_standard_1)

    # board.enforceConsistency()
    #
    # for rowI, row in enumerate(board.grid):
    #     for colI, node in enumerate(row):
    #         if node.hasFinalValue():
    #             baseBoard.grid[rowI][colI] = list(node.possibleValues)[0]
    #
    # baseBoard.print_board()


    # Full CSP solver w/ backtracking, MRV and LCV

    # Heap which orders nodes based on their remaining possible values
    MRVHeap = board.getAllNodes()
    heapify(MRVHeap)

    progressMade = True
    while progressMade:
        progressMade = False
        # Take the node with the fewest remaining possible values (MRV)
        current = heappop(MRVHeap)

        # Make the move which will result in the fewest restrictions on neighbors (LCV)
        LCV = None
        minConstraints = float('inf')  # Infinity
        for val in current.possibleValues:
            # TODO Calculate the number of restrictions made on neighbors for each value
            pass

        copyBoard = board.makeMove(current, LCV)

        consistent = copyBoard.enforceConsistency()
        if consistent:
           pass


if __name__ == "__main__":
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(directory, "data", "puzzle_standard_1.txt")

    start = time.perf_counter()
    BaseBoard = SudokuBoard(file_path)
    end = time.perf_counter()
    print(f"{end - start} seconds")

    solve(BaseBoard)