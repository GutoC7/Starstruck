from enum import IntEnum
from typing import List, Tuple, Set

class CellState(IntEnum):
    EMPTY = 0
    STAR = 1
    MARK = 2

class StarstruckEngine:
    def __init__(self, size: int, regions: List[List[int]]):
        self.size = size
        self.regions = regions
        self.board = [[CellState.EMPTY for _ in range(size)] for _ in range(size)]
        self.stars: Set[Tuple[int, int]] = set()

    def clear(self):
        """Resets the board to an initial empty state."""
        self.board = [[CellState.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.stars.clear()

    def _auto_mark(self, r: int, c: int):
        """Marks the row, column, and 8-neighbors as impossible."""
        # Row and Column
        for i in range(self.size):
            if self.board[r][i] == CellState.EMPTY: self.board[r][i] = CellState.MARK
            if self.board[i][c] == CellState.EMPTY: self.board[i][c] = CellState.MARK
            
        # 8-way Adjacency
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if self.board[nr][nc] == CellState.EMPTY:
                        self.board[nr][nc] = CellState.MARK

    def toggle_star(self, r: int, c: int):
        if self.board[r][c] == CellState.STAR:
            self.board[r][c] = CellState.EMPTY
            self.stars.remove((r, c))
        else:
            self.board[r][c] = CellState.STAR
            self.stars.add((r, c))
            self._auto_mark(r, c)

    def toggle_mark(self, r: int, c: int):
        if self.board[r][c] == CellState.MARK:
            self.board[r][c] = CellState.EMPTY
        elif self.board[r][c] == CellState.EMPTY:
            self.board[r][c] = CellState.MARK

    def get_conflicts(self) -> Set[Tuple[int, int]]:
        conflicts = set()
        row_counts = [0] * self.size
        col_counts = [0] * self.size
        region_counts = [0] * self.size
        
        for r, c in self.stars:
            row_counts[r] += 1
            col_counts[c] += 1
            region_counts[self.regions[r][c]] += 1
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        if (nr, nc) in self.stars:
                            conflicts.add((r, c))
                            conflicts.add((nr, nc))
                            
        for r, c in self.stars:
            if row_counts[r] > 1 or col_counts[c] > 1 or region_counts[self.regions[r][c]] > 1:
                conflicts.add((r, c))
                
        return conflicts

    def is_solved(self) -> bool:
        return len(self.stars) == self.size and len(self.get_conflicts()) == 0