import os
import time

from collections import deque

from sudoku_board import SudokuBoard

ONE_TO_NINE = {1, 2, 3, 4, 5, 6, 7, 8 ,9}

class CSPNode:
    """
    Represents one cell on the sudoku board, and supports common CSP operations w/ error checking
    """
    nodeId : int
    assignedValue : int | None
    domain : set[int]
    possibleValues : set[int]
    neighbors : set

    def __init__(self, nodeId : int, domain : set[int], assignedValue : int =None):
        """
        Create a new CSP node. Initializes with no neighbors, which means assign it values has no effect on other nodes.
        :param nodeId: The nodeId of this node. Used to equate cells in the same position on different copies of the same board
        :param domain: The complete range of available numbers for this cell to take on. Expected to be a range from
            one to nine unless this cell is given a certain value by the puzzle
        :param assignedValue: The value currently assigned to this cell
        """
        self.nodeId = nodeId
        self.assignedValue = assignedValue
        self.domain = domain
        self.possibleValues = domain.copy()
        self.neighbors = set()

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

    def addNeighbors(self, *neighborsToAdd):
        """
        Add a collection of nodes as neighbors to this node, meaning this node's assigned value will affect their
        possible values.
        :param neighborsToAdd: A collection of CSPNodes
        :return: None
        """
        self.neighbors.update(neighborsToAdd)
        self.neighbors.difference_update([self])

    def assignValue(self, value : int):
        """
        Assign a value to this node
        :param value: The value to add. Ignored if not in the current possibilities
        :return: None
        """
        if value in self.possibleValues:
            self.assignedValue = value
            self.possibleValues.union([value])
        else:
            print(f"CSP: Tried to assign invalid value ({value}) to node with available domain {self.possibleValues}")

    def restrict(self, *restrictions) -> bool:
        """
        Restrict the values which are valid for this node
        :param restrictions: A collection of values to restrict
        :return: Whether the restrictions removed any values no previously restricted
        """
        prevLen = len(self.possibleValues)
        self.possibleValues.difference_update(restrictions)
        restrictionMade = len(self.possibleValues) < prevLen

        return restrictionMade

    def copy(self):
        """
        Return a copy of this node, with the same nodeId, domain, and assignedValue(if any).
        Does not copy neighbors or restrictions on the domain.
        :return: A Deep copy of this node as described above
        """
        return CSPNode(self.nodeId, self.possibleValues, self.assignedValue)

    def getConstraintsFrom(self, val):
        """
        Get the number of constraints which would be added if this node took on val
        :param val: The value to take on
        :return: The number of constraints made if this node were to take this val
        """
        count = 0
        for neighbor in self.neighbors:
            if val in neighbor.possibleValues:
                count += 1
        return count

    def __repr__(self):
        return str(self.nodeId)

    def __hash__(self):
        return self.nodeId

    def __lt__(self, other):
        return len(self.possibleValues) - len(other.possibleValues)

class CSPBoard:
    grid : list[list[CSPNode|None]]
    size : int
    boxSize : int
    custom : bool

    def __init__(self, size:int, boxSize:int, custom:bool):
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self.size = size
        self.boxSize = boxSize
        self.custom = custom

    def getAllNodes(self):
        """
        Get a list of all cells in the grid
        :return: A list of all cells contained in the grid
        """
        allNodes = []
        for row in self.grid:
            allNodes.extend(row)
        return allNodes

    def isSolved(self):
        """
        Get whether this board is solved, i.e. every cell has an assigned value
        :return: Whether this board is solved
        """
        for node in self.getAllNodes():
            if node.assignedValue is None:
                return False
        return True

    def assignNeighbors(self):
        """
        Assign every cell in the grid neighbors according to standard sudoku rules. A cell is a neighbor with all cells
        in the same row, col, and 3x3 box.
        :return: None
        """
        for rowI, row in enumerate(self.grid):
            for colI, node in enumerate(row):
                # Same row
                node.addNeighbors(*row)
                # Same col
                node.addNeighbors(*[self.grid[row][colI] for row in range(self.size)])

                # Same box
                start_row = (rowI // self.boxSize) * self.boxSize
                start_col = (colI // self.boxSize) * self.boxSize
                for i in range(start_row, start_row + self.boxSize):
                    for j in range(start_col, start_col + self.boxSize):
                        node.addNeighbors(self.grid[i][j])
                if self.custom:
                    if rowI == colI:
                        node.addNeighbors(*[self.grid[i][i] for i in range(self.size)])
                    if rowI + colI == self.size - 1:
                        node.addNeighbors(*[self.grid[i][self.size - 1 - i] for i in range(self.size)])

    def copy(self):
        """
        Create a copy of this board, keeping neighbors but not restrictions on possible values (currently(11/7))
        :return: The created copy
        """
        copy = CSPBoard(self.size, self.boxSize, self.custom)
        for i, row in enumerate(self.grid):
            for j, node in enumerate(row):
                copy.grid[i][j] = node.copy()
        copy.assignNeighbors()
        return copy

    def makeMove(self, cellToChange : CSPNode, val : int):
        """
        Create a copy of this board where one cell is assigned a certain value
        :param cellToChange: The cell to assign a value to
        :param val: The value to assign the cell
        :return: The board with the newly assigned value
        """
        copyBoard = self.copy()

        for node in copyBoard.getAllNodes():
            if node.nodeId == cellToChange.nodeId:
                node.assignValue(val)

        return copyBoard

    def enforceConsistency(self) -> bool:
        """
        An implementation of a forward-checking algorithm.
        This restricts values from a node's possible values list based on its neighbors' values, or impossible
        restrictions certain values would place on its neighbors' possible values.
        :return: Whether this configuration is satisfiable.
        """
        stillToCheck = deque()

        stillToCheck.extend([node for node in self.getAllNodes() if node.assignedValue is None])

        inQueue = set(stillToCheck)

        while len(stillToCheck) > 0:
            current = stillToCheck.popleft()
            inQueue.remove(current)

            revised = False
            for neighbor in current.neighbors:
                # Add bad vals to this set for removal later so the set doesn't change while under iteration
                invalidVals = set()
                for value in current.possibleValues:
                    if (value in neighbor.possibleValues and neighbor.hasFinalValue()) or value == neighbor.assignedValue:
                        # Assigning value to current would leave neighbor with no possible values
                        invalidVals.add(value)
                        revised = True
                current.restrict(*invalidVals)

            if revised:
                if current.isDeadEnd():
                    return False
                if current.hasFinalValue():
                    current.assignValue(list(current.possibleValues)[0])
                # Re-check all neighbors not already in the queue against this revised domain
                recheck = set([n for n in current.neighbors if n not in inQueue and n.assignedValue is None])
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

def convertToCSP(baseBoard : SudokuBoard) -> CSPBoard:
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
                node = CSPNode(nodeId,{value}, assignedValue=value)
            else:
                node = CSPNode(nodeId, ONE_TO_NINE.copy())
            board.grid[i][j] = node
            nodeId += 1

    board.assignNeighbors()

    return board


def solve(baseBoard : SudokuBoard):
    """
    Solve the given SudokuBoard, if possible
    Prints a possible solution if one exists, or "No Solution" if the given board is unsolvable
    :param baseBoard: The board to solve
    :return: None
    """
    configsGenerated = configsProcessed = 1
    board = convertToCSP(baseBoard)
    solvable = board.enforceConsistency()

    configStack = [board]
    solved = False

    if solvable:
        while len(configStack) > 0 and not solved:
            currentConfig = configStack.pop()
            configsProcessed += 1
            # print(currentConfig)

            # Get the MRV - Nodes are compared based on size of their possible values list
            currentNode = min([node for node in currentConfig.getAllNodes() if node.assignedValue is None])

            # Sort possible values of the MRV to find the LCV
            orderedMoveList = list(currentNode.possibleValues)
            orderedMoveList.sort(key=lambda x:currentNode.getConstraintsFrom(x))

            for val in orderedMoveList:
                newConfig = currentConfig.makeMove(currentNode, val)
                configsGenerated += 1
                valid = newConfig.enforceConsistency()
                if valid:
                    if newConfig.isSolved():
                        solved = True
                        break
                    configStack.append(newConfig)

    print(f"Solved\n{newConfig}" if solved else "No Solution")
    print(f"Configs Made:{configsGenerated}")
    print(f"Configs Processed:{configsProcessed}")

if __name__ == "__main__":
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # custom = False
    # file_path = os.path.join(directory, "data", "puzzle_standard_1.txt")
    # file_path = os.path.join(directory, "data", "puzzle_hard.txt")
    file_path = os.path.join(directory, "data", "puzzle_custom_2.txt")
    custom = True

    start = time.perf_counter()

    BaseBoard = SudokuBoard(file_path, custom)
    solve(BaseBoard)

    end = time.perf_counter()

    print(f"{end - start} seconds")