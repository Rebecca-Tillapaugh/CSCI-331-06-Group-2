# Project 4 - Customized Sudoku Solver Project

## Abstract
This project implements a solver for a **Customized Sudoku Puzzle** using **constraint satisfaction techniques (CSP)**. The solver includes two algorithms:  
1. **Plain Backtracking** – a traditional recursive solver without constraint propagation.  
2. **CSP Enhanced Backtracking** – backtracking with techniques like forward checking, arc consistency, and domain pruning to improve efficiency.  

The project allows experimenting with customized Sudoku variants and comparing the performance of both algorithms on these puzzles.  

## Developers
| Name | Contribution |
|------|-------------|
| Marvynn Talusan    | Implemented Sudoku board class, basic utilities, and file handling |
| Lucas Peterson     | Implemented CSP Enhanced Backtracking solver (CSPNode structure, enforceConsistency) |
| Rebecca Tillapaugh | Implemented Backtracking solver and testing framework, performance analysis |

## How to Run the Project

### Prerequisites
- Python 3.10+

### Steps to Run
1. Clone the repository:
```bash
git clone https://github.com/Rebecca-Tillapaugh/CSCI-331-06-Group-2.git
cd <repository_folder>