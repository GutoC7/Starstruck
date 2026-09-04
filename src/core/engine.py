from enum import IntEnum
from typing import List, Tuple, Set

class CellState(IntEnum):
    EMPTY = 0
    STAR = 1
    MARK = 2  # The 'X' players place to rule out impossible cells

class StarstruckEngine:
    def __init__(self, size: int, regions: List[List[int]]):
        self.size = size
        self.regions = regions
        
        # 2D array representing the visual state of the grid
        self.board = [[CellState.EMPTY for _ in range(size)] for _ in range(size)]
        
        # O(1) lookup set for star positions to optimize conflict checking
        self.stars: Set[Tuple[int, int]] = set()

    def toggle_star(self, r: int, c: int):
        """Toggles a cell between EMPTY and STAR."""
        if self.board[r][c] == CellState.STAR:
            self.board[r][c] = CellState.EMPTY
            self.stars.remove((r, c))
        else:
            self.board[r][c] = CellState.STAR
            self.stars.add((r, c))

    def toggle_mark(self, r: int, c: int):
        """Toggles a cell between EMPTY and MARK ('X')."""
        if self.board[r][c] == CellState.MARK:
            self.board[r][c] = CellState.EMPTY
        elif self.board[r][c] == CellState.EMPTY:
            self.board[r][c] = CellState.MARK

    def get_conflicts(self) -> Set[Tuple[int, int]]:
        """
        Calculates and returns a set of (row, col) coordinates for all stars 
        that currently violate any game constraints.
        """
        conflicts = set()
        
        row_counts = [0] * self.size
        col_counts = [0] * self.size
        region_counts = [0] * self.size
        
        # Tally up the constraints
        for r, c in self.stars:
            row_counts[r] += 1
            col_counts[c] += 1
            region_counts[self.regions[r][c]] += 1
            
            # Check King's move (8-way adjacency)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        if (nr, nc) in self.stars:
                            conflicts.add((r, c))
                            conflicts.add((nr, nc))
                            
        # Check linear and regional limits
        for r, c in self.stars:
            if row_counts[r] > 1 or col_counts[c] > 1 or region_counts[self.regions[r][c]] > 1:
                conflicts.add((r, c))
                
        return conflicts

    def is_solved(self) -> bool:
        """Returns True if the puzzle has exactly 'size' stars and 0 conflicts."""
        return len(self.stars) == self.size and len(self.get_conflicts()) == 0