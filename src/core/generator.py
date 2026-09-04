import random
from typing import List, Tuple, Optional
from .solver import StarBattleSolver

class PuzzleGenerator:
    def __init__(self, size: int):
        self.size = size

    def _generate_seed_stars(self) -> List[Tuple[int, int]]:
        """Places N stars using DFS backtracking to guarantee a valid hidden solution."""
        stars: List[Tuple[int, int]] = []
        col_used = [False] * self.size
        
        def place_star(row: int) -> bool:
            if row == self.size:
                return True
            
            cols = list(range(self.size))
            random.shuffle(cols)
            
            for col in cols:
                if col_used[col]:
                    continue
                
                conflict = False
                for r, c in stars:
                    if abs(r - row) <= 1 and abs(c - col) <= 1:
                        conflict = True
                        break
                        
                if conflict:
                    continue
                
                stars.append((row, col))
                col_used[col] = True
                
                if place_star(row + 1):
                    return True
                    
                stars.pop()
                col_used[col] = False
                
            return False
            
        place_star(0)
        return stars

    def _grow_regions(self, stars: List[Tuple[int, int]], hard_mode: bool) -> Optional[List[List[int]]]:
        regions = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        frontier: List[Tuple[int, int, int]] = []
        region_sizes = {i: 0 for i in range(self.size)}
        
        # 1. Place the initial seed stars
        for region_id, (r, c) in enumerate(stars):
            regions[r][c] = region_id
            region_sizes[region_id] += 1
            
        if hard_mode:
            # PHASE 1: Forced Survival Expansion
            # Make every region grab up to 2 random neighbors immediately to prevent 1-cell traps
            for region_id, (r, c) in enumerate(stars):
                neighbors = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                        neighbors.append((nr, nc))
                
                random.shuffle(neighbors)
                for nr, nc in neighbors[:2]:
                    if regions[nr][nc] == -1: # Double check it wasn't just claimed
                        regions[nr][nc] = region_id
                        region_sizes[region_id] += 1

        # PHASE 2: Populate the frontier with the edges of our new shapes
        for r in range(self.size):
            for c in range(self.size):
                if regions[r][c] != -1:
                    region_id = regions[r][c]
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                            frontier.append((nr, nc, region_id))
                            
        # PHASE 3: Pure Random BFS for jagged, organic shapes
        while frontier:
            idx = random.randint(0, len(frontier) - 1)
            r, c, region_id = frontier.pop(idx)
            
            if regions[r][c] == -1:
                regions[r][c] = region_id
                region_sizes[region_id] += 1
                
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                        frontier.append((nr, nc, region_id))
                        
        # STRICT REJECTION: Still enforce the minimum size rule
        if hard_mode and any(size < 3 for size in region_sizes.values()):
            return None
                
        return regions

    def generate(self) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
        """Generates layouts until it finds one with exactly 1 unique solution."""
        attempts = 0
        hard_mode = self.size >= 9  # Automatically trigger balanced growth on 9x9 grids
        
        while True:
            attempts += 1
            stars = self._generate_seed_stars()
            regions = self._grow_regions(stars, hard_mode)
            
            # If the board was rejected for having tiny regions, try again
            if regions is None:
                continue
            
            solver = StarBattleSolver(self.size, regions)
            
            if solver.count_solutions(max_count=2) == 1:
                print(f"[{'HARD' if hard_mode else 'EASY'}] Puzzle generated successfully after {attempts} attempt(s).")
                return regions, stars