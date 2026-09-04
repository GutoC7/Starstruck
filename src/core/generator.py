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
        """Grows regions using either random BFS (Easy) or size-balanced Priority BFS (Hard)."""
        regions = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        frontier: List[Tuple[int, int, int]] = []
        
        # Track the cell count of each region to balance growth
        region_sizes = {i: 1 for i in range(self.size)}
        
        for region_id, (r, c) in enumerate(stars):
            regions[r][c] = region_id
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if 0 <= r + dr < self.size and 0 <= c + dc < self.size:
                    frontier.append((r + dr, c + dc, region_id))
                    
        while frontier:
            if hard_mode:
                # 1. Identify active regions currently in the frontier
                active_regions = set(f[2] for f in frontier)
                
                # 2. Find the smallest size among those active regions
                min_size = min(region_sizes[r_id] for r_id in active_regions)
                
                # 3. Filter frontier to ONLY include candidates from the smallest regions
                candidates = [i for i, f in enumerate(frontier) if region_sizes[f[2]] == min_size]
                
                # 4. Pick randomly from the smallest to maintain organic shapes
                idx = random.choice(candidates)
            else:
                # Easy mode: Pure random growth
                idx = random.randint(0, len(frontier) - 1)
            
            r, c, region_id = frontier.pop(idx)
            
            if regions[r][c] == -1:
                regions[r][c] = region_id
                region_sizes[region_id] += 1
                
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and regions[nr][nc] == -1:
                        frontier.append((nr, nc, region_id))
                        
        # STRICT REJECTION: If any region is 1 or 2 cells large, reject this layout entirely.
        if hard_mode:
            if any(size < 3 for size in region_sizes.values()):
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