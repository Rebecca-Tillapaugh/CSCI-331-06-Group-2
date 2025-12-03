import os
import time
from collections import deque

from sudoku_board import SudokuBoard

ONE_TO_NINE = {1, 2, 3, 4, 5, 6, 7, 8, 9}


class CSPNode:
    """
    Represents one cell on the sudoku board, and supports common CSP operations w/ error checking
    """
    cellNum: int
    assignedValue: int | None
    possibleValues: set[int]

    def __init__(self, cellNum: int, domain: set[int], assignedValue: int = None):
        """
        Create a new CSP node. Initializes with no neighbors, which means assign it values has no effect on other nodes.
        :param cellNum: The cell number of this node when read left to right top ot bottom, starting at 0
        :param domain: The range of numbers this cell is able to take on without conflicting with a neighboring cell
        :param assignedValue: The value currently assigned to this cell
        """
        self.cellNum = cellNum
        self.possibleValues = domain.copy()
        self.assignedValue = assignedValue

    def hasFinalValue(self):
        """
        Return if this node has only one possible value, given the restrictions placed on by its neighbors and any
        forward checking which has been done.
        :return: Whether this node has only one valid value
        """
        return len(self.possibleValues) == 1

    def isDeadEnd(self):
        """
        Return if this node has been determined to have no valid value, either by direct restrictions or forward
        checking.
        :return: Whether this node has no valid values
        """
        return len(self.possibleValues) == 0

    def assignValue(self, value: int):
        """
        Assign a value to this node
        :param value: The value to assign
        :return: None
        """
        self.assignedValue = value
        self.possibleValues = {value}

    def restrict(self, *restrictions):
        """
        Restrict the values which are valid for this node
        :param restrictions: A collection of values to restrict
        :return: Whether the restrictions removed any values no previously restricted
        """
        self.possibleValues.difference_update(restrictions)

    def copy(self):
        """
        Return a copy of this node, with the same nodeId, possible domain, and assignedValue(if any).
        Does not copy neighbors
        :return: A Deep copy of this node as described above
        """
        return CSPNode(self.cellNum, self.possibleValues, self.assignedValue)

    def __repr__(self):
        return str(self.cellNum)

    def __hash__(self):
        return self.cellNum

    def __lt__(self, other):
        return len(self.possibleValues) - len(other.possibleValues)


class CSPBoard:
    grid: list[list[CSPNode | None]]
    size: int
    boxSize: int
    custom: bool
    neighborsOf: dict[int, set[int]]

    def __init__(self, size: int, boxSize: int, custom: bool, neighborAssignments: dict[int, set[int]] = None):
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self.size = size
        self.boxSize = boxSize
        self.custom = custom
        self.neighborsOf = dict() if neighborAssignments is None else neighborAssignments

    def getCell(self, cellNum):
        return self.grid[cellNum // self.size][cellNum % self.size]

    def getUnassignedNodes(self):
        """
        Get a list of all cells without an assigned value in the grid
        :return: A list of all unassigned cells in the grid
        """
        unassignedNodes = []
        for row in self.grid:
            for cell in row:
                if cell.assignedValue is None:
                    unassignedNodes.append(cell)
        return unassignedNodes

    def getUnassignedNodeNums(self):
        """
        Get a list of all cell numbers without an assigned value in the grid
        :return: A list of all unassigned cells in the grid
        """
        unassignedNodes = []
        for row in self.grid:
            for cell in row:
                if cell.assignedValue is None:
                    unassignedNodes.append(cell.cellNum)
        return unassignedNodes

    def isSolved(self):
        """
        Get whether this board is solved, i.e. every cell has an assigned value
        :return: Whether this board is solved
        """
        return len(self.getUnassignedNodes()) == 0

    def assignNeighbors(self):
        """
        Assign every cell in the grid neighbors according to standard sudoku rules. A cell is a neighbor with all cells
        in the same row, col, and 3x3 box.
        :return: None
        """
        for rowI, row in enumerate(self.grid):
            for colI, node in enumerate(row):
                toAdd = set()

                # Same row
                toAdd.update(range(rowI * self.size, (rowI + 1) * self.size))
                # Same col
                toAdd.update([(rowNum * self.size) + colI for rowNum in range(self.size)])

                # Same box
                start_row = (rowI // self.boxSize) * self.boxSize
                start_col = (colI // self.boxSize) * self.boxSize
                for i in range(start_row, start_row + self.boxSize):
                    for j in range(start_col, start_col + self.boxSize):
                        toAdd.add(i * self.size + j)

                # Same diagonal for custom puzzles
                if self.custom:
                    if rowI == colI:
                        # FIXED: main diagonal indices (i * size + i), not i ** 2
                        toAdd.update([i * self.size + i for i in range(self.size)])
                    if rowI + colI == self.size - 1:
                        toAdd.update([(i * self.size) + self.size - 1 - i for i in range(self.size)])

                toAdd.difference_update({node.cellNum})
                self.neighborsOf[node.cellNum] = toAdd

    def copy(self):
        """
        Create a copy of this board, keeping neighbors and restrictions on possible values
        :return: The created copy
        """
        # FIXED: copy neighborsOf so copies don't share the same dict reference
        copy = CSPBoard(self.size, self.boxSize, self.custom, self.neighborsOf.copy())
        for i, row in enumerate(self.grid):
            for j, node in enumerate(row):
                copy.grid[i][j] = node.copy()
        return copy

    def getConstraintsFrom(self, cell, val):
        """
        Get the number of constraints which would be added if a node took on some val
        :param cell: The cellNumber of the node in question
        :param val: The value to take on
        :return: The number of constraints made if this node were to take this val
        """
        return sum([1 if val in self.getCell(n).possibleValues else 0 for n in self.neighborsOf[cell]])

    def makeMove(self, cellToChange: CSPNode, val: int):
        """
        Create a copy of this board where one cell is assigned a certain value
        :param cellToChange: The cell to assign a value to
        :param val: The value to assign the cell
        :return: The board with the newly assigned value
        """
        copyBoard = self.copy()

        rowI = cellToChange.cellNum // self.size
        colI = cellToChange.cellNum % self.size
        copyBoard.grid[rowI][colI].assignValue(val)

        return copyBoard

    def enforceConsistency(self) -> bool:
        """
        An implementation of a forward-checking algorithm.
        This restricts values from a node's possible values list based on its neighbors' values, or impossible
        restrictions certain values would place on its neighbors' possible values.
        :return: Whether this configuration is satisfiable.
        """
        stillToCheck = deque()

        stillToCheck.extend(self.getUnassignedNodeNums())

        inQueue = set(stillToCheck)

        while len(stillToCheck) > 0:
            currentNum = stillToCheck.popleft()
            inQueue.remove(currentNum)
            current = self.getCell(currentNum)

            # Add bad vals to this set for removal later so the set doesn't change while under iteration
            invalidVals = set()
            for value in current.possibleValues:
                for neighborNum in self.neighborsOf[current.cellNum]:
                    neighbor = self.getCell(neighborNum)
                    if neighbor.hasFinalValue() and value in neighbor.possibleValues:
                        # Assigning value to current would leave neighbor with no possible values
                        invalidVals.add(value)
                        break

            revised = len(invalidVals) > 0
            current.restrict(*invalidVals)

            if revised:
                if current.isDeadEnd():
                    return False
                if current.hasFinalValue():
                    current.assignValue(next(iter(current.possibleValues)))
                # Re-check all neighbors not already in the queue against this revised domain
                recheck = set([n for n in self.neighborsOf[currentNum]
                               if n not in inQueue and self.getCell(n).assignedValue is None])
                stillToCheck.extend(recheck)
                inQueue.update(recheck)
        return True

    def __repr__(self):
        result = ""
        for i, row in enumerate(self.grid):
            for j, node in enumerate(row):
                result += str(node.assignedValue) if node.assignedValue is not None else '.'
                result += " "
                result += "| " if j == 2 or j == 5 else ""
            result += "\n" + ("---------------------\n" if i == 2 or i == 5 else "")
        return result


def convertToCSP(baseBoard: SudokuBoard) -> CSPBoard:
    """
    Convert a SudokuBoard object into a CSPBoard object
    :param baseBoard: The SudokuBoard board object to convert
    :return: The converted board
    """
    board = CSPBoard(baseBoard.size, baseBoard.box_size, baseBoard.custom)
    nodeId = 0
    for i, row in enumerate(baseBoard.grid):
        for j, value in enumerate(row):
            if value != 0:
                node = CSPNode(nodeId, {value}, assignedValue=value)
            else:
                node = CSPNode(nodeId, ONE_TO_NINE.copy())
            board.grid[i][j] = node
            nodeId += 1

    board.assignNeighbors()

    return board


def solve(baseBoard: SudokuBoard):
    """
    Solve the given SudokuBoard, if possible
    Prints a possible solution if one exists, or "No Solution" if the given board is unsolvable
    Returns a dictionary of performance metrics for experiments.
    :param baseBoard: The board to solve
    :return: dict of metrics
    """

    consistency = copying = 0
    configsGenerated = configsProcessed = 0
    board = convertToCSP(baseBoard)

    configStack = [board]
    solved = False
    finalBoard = None

    while len(configStack) > 0 and not solved:
        currentConfig = configStack.pop()
        configsProcessed += 1

        start = time.perf_counter()
        consistent = currentConfig.enforceConsistency()
        consistency += time.perf_counter() - start

        if consistent:
            solved = currentConfig.isSolved()
            if solved:
                finalBoard = currentConfig
                break
            else:
                # Get the most restricted assignable vertex (MRV)
                currentNode = min(currentConfig.getUnassignedNodes())
                # LCV ordering
                orderedMoves = sorted(
                    currentNode.possibleValues,
                    key=lambda x: currentConfig.getConstraintsFrom(currentNode.cellNum, x)
                )

                start = time.perf_counter()
                for val in orderedMoves:
                    configStack.append(currentConfig.makeMove(currentNode, val))
                    configsGenerated += 1
                copying += time.perf_counter() - start

    # Print solution for verification
    print(f"Solved\n{finalBoard}" if solved else "No Solution")
    print(f"Configs Made: {configsGenerated}")
    print(f"Configs Processed: {configsProcessed}")
    print(consistency, copying, sep="\n")

    total_runtime = consistency + copying  #Approximates

    # Return metrics for experiment collection
    return {
        "solved": solved,
        "runtime": total_runtime,
        "configsProcessed": configsProcessed,
        "configsGenerated": configsGenerated,
        "consistency": consistency,
        "copying": copying,
        "finalBoard": finalBoard
    }


if __name__ == "__main__":
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    custom = False
    # file_path = os.path.join(directory, "data", "puzzle_standard_1.txt")
    file_path = os.path.join(directory, "data", "puzzle_hard.txt")
    # file_path = os.path.join(directory, "data", "puzzle_custom_2.txt")
    # custom = True

    start = time.perf_counter()

    BaseBoard = SudokuBoard(file_path, custom)
    solve(BaseBoard)

    end = time.perf_counter()

    print(f"{end - start} seconds")