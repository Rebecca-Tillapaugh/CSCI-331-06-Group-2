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
        old_len = len(self.possibleValues)
        self.possibleValues.difference_update(restrictions)
        return len(self.possibleValues) != old_len

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
        nodes = []
        for row in self.grid:
            for cell in row:
                if cell.assignedValue is None:
                    nodes.append(cell)
        return nodes

    def getUnassignedNodeNums(self):
        """
        Get a list of all cell numbers without an assigned value in the grid
        :return: A list of all unassigned cells in the grid
        """
        nums = []
        for row in self.grid:
            for cell in row:
                if cell.assignedValue is None:
                    nums.append(cell.cellNum)
        return nums

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
                toAdd.update([(r * self.size) + colI for r in range(self.size)])

                # Same box
                start_r = (rowI // self.boxSize) * self.boxSize
                start_c = (colI // self.boxSize) * self.boxSize
                for i in range(start_r, start_r + self.boxSize):
                    for j in range(start_c, start_c + self.boxSize):
                        toAdd.add(i * self.size + j)

                # Same diagonal for custom puzzles
                if self.custom:
                    if rowI == colI:
                        toAdd.update([i * self.size + i for i in range(self.size)])
                    if rowI + colI == self.size - 1:
                        toAdd.update([(i * self.size) + (self.size - 1 - i) for i in range(self.size)])

                toAdd.discard(node.cellNum)
                self.neighborsOf[node.cellNum] = toAdd

    def copy(self):
        """
        Create a copy of this board, keeping neighbors and restrictions on possible values
        :return: The created copy
        """
        copy = CSPBoard(self.size, self.boxSize, self.custom, self.neighborsOf.copy())
        for i, row in enumerate(self.grid):
            for j, node in enumerate(row):
                copy.grid[i][j] = node.copy()
        return copy

    def getConstraintsFrom(self, cellNum, val):
        """
        Get the number of constraints which would be added if a node took on some val
        :param cell: The cellNumber of the node in question
        :param val: The value to take on
        :return: The number of constraints made if this node were to take this val
        """
        return sum([
            1 if val in self.getCell(n).possibleValues else 0
            for n in self.neighborsOf[cellNum]
        ])

    def makeMove(self, node: CSPNode, val: int):
        """
        Create a copy of this board where one cell is assigned a certain value
        :param cellToChange: The cell to assign a value to
        :param val: The value to assign the cell
        :return: The board with the newly assigned value
        """
        newBoard = self.copy()
        r = node.cellNum // self.size
        c = node.cellNum % self.size
        newBoard.grid[r][c].assignValue(val)
        return newBoard

    def enforceConsistency(self):
        """
        An implementation of a Forward-Checking (FC) algorithm.
        This restricts values from unassigned neighbors based on ALL currently assigned nodes.
        :return: Whether this configuration is satisfiable.
        """
        assigned_nodes = [
            node for row in self.grid for node in row if node.assignedValue is not None
        ]

        # for every assigned node, remove its value from its unassigned neighbors domains
        for assigned_node in assigned_nodes:
            val = assigned_node.assignedValue
            
            # Check all its neighbors
            for neighNum in self.neighborsOf[assigned_node.cellNum]:
                neighbor_node = self.getCell(neighNum)

                # Only restrict unassigned nodes
                if neighbor_node.assignedValue is None:
                    
                    # If a restriction occurs 
                    if neighbor_node.restrict(val):

                        # Dead end here
                        if neighbor_node.isDeadEnd():
                            return False #Pruning it

        return True


def convertToCSP(baseBoard: SudokuBoard) -> CSPBoard:
    """
    Convert a SudokuBoard object into a CSPBoard object
    :param baseBoard: The SudokuBoard board object to convert
    :return: The converted board
    """
    board = CSPBoard(baseBoard.size, baseBoard.box_size, baseBoard.custom)
    nodeId = 0
    for i, row in enumerate(baseBoard.grid):
        for j, val in enumerate(row):
            domain = {val} if val != 0 else ONE_TO_NINE.copy()
            node = CSPNode(nodeId, domain, assignedValue=val if val != 0 else None)
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

    consistency_time = 0
    copying_time = 0
    configsGenerated = 0
    configsProcessed = 0

    board = convertToCSP(baseBoard)
    stack = [board]
    solved = False
    finalBoard = None

    while stack and not solved:
        current = stack.pop()
        configsProcessed += 1

        # Forward checking
        t0 = time.perf_counter()
        consistent = current.enforceConsistency()
        consistency_time += time.perf_counter() - t0

        if not consistent:
            continue

        if current.isSolved():
            solved = True
            finalBoard = current
            break

        # Pick MRV
        node = min(current.getUnassignedNodes())

        # LCV ordering
        ordered = sorted(
            node.possibleValues,
            key=lambda v: current.getConstraintsFrom(node.cellNum, v)
        )

        # Generate child boards
        t1 = time.perf_counter()
        for v in ordered:
            stack.append(current.makeMove(node, v))
            configsGenerated += 1
        copying_time += time.perf_counter() - t1

    total_runtime = consistency_time + copying_time

    return {
        "solved": solved,
        "runtime": total_runtime,
        "configsProcessed": configsProcessed,
        "configsGenerated": configsGenerated,
        "consistency_time": consistency_time,
        "copying_time": copying_time,
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