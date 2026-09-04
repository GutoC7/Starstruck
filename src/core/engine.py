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
        
        # New: Queue to hold groups of cells to mark, ordered by distance
        self.animation_queue: List[List[Tuple[int, int]]] = []

    def clear(self):
        self.board = [[CellState.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.stars.clear()
        self.animation_queue.clear()

    def _auto_mark(self, r: int, c: int):
        """Calculates marks and queues them sequentially based on distance."""
        pending_marks = {}
        
        for i in range(self.size):
            # Row expansion
            if self.board[r][i] == CellState.EMPTY:
                dist = abs(c - i)
                if dist not in pending_marks: pending_marks[dist] = []
                pending_marks[dist].append((r, i))
            
            # Column expansion
            if self.board[i][c] == CellState.EMPTY:
                dist = abs(r - i)
                if dist not in pending_marks: pending_marks[dist] = []
                pending_marks[dist].append((i, c))
                
        # 8-way Adjacency (Force into distance 1)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if self.board[nr][nc] == CellState.EMPTY:
                        if 1 not in pending_marks: pending_marks[1] = []
                        if (nr, nc) not in pending_marks[1]:
                            pending_marks[1].append((nr, nc))
                            
        # Push to the animation queue sorted by distance
        for d in sorted(pending_marks.keys()):
            self.animation_queue.append(pending_marks[d])

    def process_animation_step(self):
        """Pops the next distance group and marks them on the board."""
        if self.animation_queue:
            step_cells = self.animation_queue.pop(0)
            for r, c in step_cells:
                if self.board[r][c] == CellState.EMPTY:
                    self.board[r][c] = CellState.MARK

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