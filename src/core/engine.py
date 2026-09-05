from enum import IntEnum
from typing import List, Tuple, Set

class CellState(IntEnum):
    EMPTY = 0
    STAR = 1
    MARK = 2

class StarstruckEngine:
    # Now accepts the pre-calculated solution
    def __init__(self, size: int, regions: List[List[int]], solution: List[Tuple[int, int]] = None):
        self.size = size
        self.regions = regions
        
        # Convert solution to a set for O(1) hash map lookups
        self.solution = set(tuple(s) for s in solution) if solution else set()
        
        self.board = [[CellState.EMPTY for _ in range(size)] for _ in range(size)]
        self.stars: Set[Tuple[int, int]] = set()
        self.animation_queue: List[List[Tuple[int, int]]] = []
        self.action_stack: List[Tuple[List[List[CellState]], Set[Tuple[int, int]]]] = []

    def clear(self):
        self.board = [[CellState.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.stars.clear()
        self.animation_queue.clear()
        self.action_stack.clear()

    def push_state(self):
        board_copy = [row[:] for row in self.board]
        stars_copy = set(self.stars)
        self.action_stack.append((board_copy, stars_copy))

    def undo(self):
        if self.action_stack:
            last_board, last_stars = self.action_stack.pop()
            self.board = last_board
            self.stars = last_stars
            self.animation_queue.clear()

    def get_hint(self):
        """O(1) hint system using the known mathematical solution."""
        if not self.solution:
            return
            
        self.push_state()
        
        # 1. Correct a mistake if the player made one
        wrong_stars = self.stars - self.solution
        if wrong_stars:
            r, c = next(iter(wrong_stars))
            self.board[r][c] = CellState.MARK  # Auto-cross out the mistake
            self.stars.remove((r, c))
            return
            
        # 2. If no mistakes, reveal one correct star
        missing_stars = self.solution - self.stars
        if missing_stars:
            r, c = next(iter(missing_stars))
            self.board[r][c] = CellState.STAR
            self.stars.add((r, c))
            self._auto_mark(r, c)

    def _auto_mark(self, r: int, c: int):
        pending_marks = {}
        placed_region = self.regions[r][c]
        
        for i in range(self.size):
            if self.board[r][i] == CellState.EMPTY:
                dist = abs(c - i)
                if dist not in pending_marks: pending_marks[dist] = []
                pending_marks[dist].append((r, i))
            
            if self.board[i][c] == CellState.EMPTY:
                dist = abs(r - i)
                if dist not in pending_marks: pending_marks[dist] = []
                pending_marks[dist].append((i, c))
                
        for nr in range(self.size):
            for nc in range(self.size):
                if self.board[nr][nc] == CellState.EMPTY:
                    is_adjacent = abs(nr - r) <= 1 and abs(nc - c) <= 1
                    is_same_region = self.regions[nr][nc] == placed_region
                    
                    if is_adjacent or is_same_region:
                        dist = abs(nr - r) + abs(nc - c)
                        if is_adjacent or dist == 0: 
                            dist = 1
                            
                        if dist not in pending_marks: pending_marks[dist] = []
                        if (nr, nc) not in pending_marks[dist]:
                            pending_marks[dist].append((nr, nc))
                            
        for d in sorted(pending_marks.keys()):
            self.animation_queue.append(pending_marks[d])

    def process_animation_step(self):
        if self.animation_queue:
            step_cells = self.animation_queue.pop(0)
            for r, c in step_cells:
                if self.board[r][c] == CellState.EMPTY:
                    self.board[r][c] = CellState.MARK

    def toggle_star(self, r: int, c: int):
        self.push_state()
        if self.board[r][c] == CellState.STAR:
            self.board[r][c] = CellState.EMPTY
            self.stars.remove((r, c))
        else:
            self.board[r][c] = CellState.STAR
            self.stars.add((r, c))
            self._auto_mark(r, c)

    def toggle_mark(self, r: int, c: int):
        self.push_state()
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